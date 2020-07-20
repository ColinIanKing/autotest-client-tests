#!/bin/bash
#
# Copyright (C) 2020 Canonical
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Author: Manoj Iyer <manoj.iyer@canonical.com>
#

set -e
set -E

test_iterations=3

cleanup_on_exit() {
	local rc=${?}
	trap - EXIT # prevent reinvocations
	if [ "${rc}" -ne 0 ]; then
		echo "ERROR: Script failed (${rc})" >&2
	fi
	rm -f /tmp/iperf3-config.json &>/dev/null || true
	rm -f "${logfiles[@]}" || true
	killall -9 iperf3 &>/dev/null || true
	sudo ip link set dev $client_iface down &>/dev/null || true
	sudo ip netns exec 2xgd ip link set $server_iface netns 1 &>/dev/null || true
	sudo ip netns delete 2xgd &>/dev/null || true
	sudo service irqbalance start &>/dev/null || true
	sudo /usr/bin/cpupower frequency-set -g powersave >/dev/null
}
trap cleanup_on_exit EXIT

error() {
	local lineno="$1"
	local exit_code="${3:-1}"
	echo "Error: in line: ${lineno}, exiting with status: ${exit_code}"
	exit "${exit_code}"
}
trap 'error ${LINENO}' ERR

usage() {
	cat <<-EOF
	$0: -c|--config <test config yaml> [-h|--help -t|--tune]
	-c|--config)	iperf3 test config yaml file.
	-h|--help)	this help message.
	EOF
	exit 1
}

NO_OPT_ARGS=("help")
WITH_OPT_ARGS=("config")
if ! opts=$(getopt --longoptions "$(printf "%s," "${NO_OPT_ARGS[@]}")" --longoptions "$(printf "%s:," "${WITH_OPT_ARGS[@]}")" --name "$(basename "$0")" --options "hc:" -- "$@") ; then
	usage
fi
eval set --$opts

while [[ $# -gt 0 ]]; do
	case $1 in
		-c|--config)	test_config=$2;shift;;
		-h|--help)	usage;;
		(--) shift; break ;;
		(-*) echo "$0: Error - unrecognized option $1" 1>&2; usage; exit 1;;
		(*) break ;;
	esac
	shift
done

# Install script dependencies if they don't already exist
for package in gdb jq python3-yaml iperf3 numactl; do
	if [ $(dpkg-query -W -f='${Status}' $package 2>/dev/null | grep -c "ok installed") -eq 0 ]; then
		sudo apt install -y "${package}"
	fi
done

# setup environment variables
python3 -c 'import sys, yaml, json; json.dump(yaml.load(sys.stdin, Loader=yaml.SafeLoader), sys.stdout, indent=4)' < ${test_config} > /tmp/iperf3-config.json
content=$(cat /tmp/iperf3-config.json | jq  '.setup' | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]")
export $content
server_numa_node="$(cat /sys/class/net/$server_iface/device/numa_node)"
client_numa_node="$(cat /sys/class/net/$client_iface/device/numa_node)"


# Host tuning based on info in fastdata.es.net and Mellanox.
sudo service irqbalance stop
sudo /usr/bin/cpupower frequency-set -g performance > /dev/null

# Setup client/server ip address based on Spec.
sudo ip netns add 2xgd
sudo ip netns exec 2xgd ip link set dev lo up
sudo ip link set netns 2xgd $server_iface
sudo ip netns exec 2xgd ip addr add dev $server_iface $server_ip/24
sudo ip netns exec 2xgd ip link set dev $server_iface up
sudo ip netns exec 2xgd ip link set dev $server_iface mtu 9000
sudo ip addr add dev $client_iface $client_ip/24
sudo ip link set dev $client_iface up
sudo ip link set dev $client_iface mtu 9000

echo " ++ Server interface $server_iface settings ++"
sudo ip netns exec 2xgd ip link show $server_iface

echo " ++ Client interface $client_iface settings ++"
ip link show $client_iface

# Run the tests
do_iteration() {
	local iteration="$1"
	while IFS='' read -r tests; do
		if [ "$tests" == "setup" ]; then
			continue
		fi

		unset iperf3_instances
		unset server_args
		unset client_args
		iperf3_instances=$(cat /tmp/iperf3-config.json | jq --arg test "${tests}" --arg nt "numinstances" '.[$test][$nt]')
		server_args=$(cat /tmp/iperf3-config.json | jq --arg test "${tests}" --arg so "serveroptions" '.[$test][$so]' | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" | sed 's/[^ ]* */--&/g' | sed 's/=null/ /' | tr '"\r\n' ' ')
		client_args=$(cat /tmp/iperf3-config.json | jq --arg test "${tests}" --arg co "clientoptions" '.[$test][$co]' | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" | sed 's/[^ ]* */--&/g' | sed 's/=null/ /' |  tr '"\r\n' ' ')

		echo " ++ Running $tests iteration $iteration: $iperf3_instances iperf3 instances with client options: $client_args ++"

		pids=()
		logfiles=()
		count=0
		if [ $iperf3_instances -gt 1 ]; then
			# Start server in background as a daemon
			end_port=$((start_port+$(((iperf3_instances-1)*100))))
			for port in $(seq $start_port 100 $end_port); do
				numactl -m $server_numa_node -N $server_numa_node sudo ip netns exec 2xgd iperf3 -s ${server_args} -B $server_ip -p $port -D
			done

			# Start Client 
			for port in $(seq $start_port 100 $end_port); do
				logfiles[${count}]="$(mktemp)"
				numactl -m $client_numa_node  -N $client_numa_node iperf3 ${client_args} -c $server_ip -B $client_ip  -p $port --logfile "${logfiles[${count}]}" &

				pids[${count}]=$!
				let ++count
			done
		else
			logfiles[0]="$(mktemp)"
			# Start server in background as a daemon
			numactl -m $server_numa_node -N $server_numa_node sudo ip netns exec 2xgd iperf3 -s ${server_args} -B $server_ip -p $start_port -D

			# Start Client 
			numactl -m $client_numa_node -N $client_numa_node iperf3 ${client_args} -c $server_ip -B $client_ip -p $start_port --logfile "${logfiles[0]}"
			pids[0]=$!
		fi

		# Wait for clients to finish
		for pid in ${pids[*]}; do
			wait $pid
		done
		# Purge any iperf3 before we loop around to next test.
		# and we can ignore it if nothing is killed.
		sleep 5s; sync; 
		killall -9 iperf3 &>/dev/null || true

		# Print test results. All calculations and information printed
		# are based on autotest ubuntu_performance_iperf (iperf2) tests.
		protocol=$(jq -r '.start.test_start.protocol' "${logfiles[0]}" | uniq)
		if [ "${protocol}" != "TCP" ]; then
			echo "FAILED\nUnsupported protocol ${protocol}"
			exit 1
		fi
		bps_rx=()
		bps_tx=()
		bps_rx_tot=0
		bps_tx_tot=0
		avg_bps_rx=0
		avg_bps_tx=0
		max_bps_rx=0
		min_bps_rx=0
		max_bps_tx=0
		min_bps_tx=0
		err_bps_rx=0
		err_bps_tx=0
		config_title=$(jq -r '.title' "${logfiles[0]}" | uniq)
		direction="forward"
		if [ $(jq -r '.start.test_start.reverse' "${logfiles[0]}" | uniq) -ne 0 ]; then
			direction="reverse"
		fi
		i=0
		for log in "${logfiles[@]}"; do
			bps=$(jq -r '.end.sum_received.bits_per_second' "${log}")
			printf "iperf3_%s_clients%d_instance%d_%s_%s_mbit_per_sec[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${i}" "${direction}" "receiver_rate" "${iteration}" $(bc -l <<< "scale=2; ${bps}/1000000")
			bps_rx=("${bps_rx[@]}" "$bps")
			bps_rx_tot=$(bc -l <<< "$bps_rx_tot + $bps")
			let ++i
		done
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${direction}" "receiver_total" "${iteration}" $(bc -l <<< "scale=2; ${bps_rx_tot}/1000000")
		i=0
		for log in "${logfiles[@]}"; do
		        bps=$(jq -r '.end.sum_sent.bits_per_second' "${log}")
			printf "iperf3_%s_clients%d_instance%d_%s_%s_mbit_per_sec[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${i}" "${direction}" "sender_rate" "${iteration}" $(bc -l <<< "scale=2; ${bps}/1000000")
			bps_tx=("${bps_tx[@]}" "$bps")
			bps_tx_tot=$(bc -l <<< "$bps_tx_tot + $bps")
			let ++i
		done
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${direction}" "sender_total" "${iteration}" $(bc -l <<< "scale=2; ${bps_tx_tot}/1000000")
		avg_bps_tx=$(bc -l <<< "$bps_tx_tot/${#bps_tx[@]}")
		avg_bps_rx=$(bc -l <<< "$bps_rx_tot/${#bps_rx[@]}")
		min_bps_tx=$(echo "${bps_tx[*]}" | tr ' ' '\n' | sort -nr | tail -n1)
		min_bps_rx=$(echo "${bps_rx[*]}" | tr ' ' '\n' | sort -nr | tail -n1)
		max_bps_tx=$(echo "${bps_tx[*]}" | tr ' ' '\n' | sort -nr | head -n1)
		max_bps_rx=$(echo "${bps_rx[*]}" | tr ' ' '\n' | sort -nr | head -n1)
		err_bps_tx=$(bc -l <<< "scale=5; ($max_bps_tx-$min_bps_tx)/$avg_bps_tx*100")
		err_bps_rx=$(bc -l <<< "scale=5; ($max_bps_rx-$min_bps_rx)/$avg_bps_rx*100")
		# Max throughput for Mellanox nic on DGX2 is 100G, 
		expected_throughput=$(bc -l <<< "scale=5; 100000000000*0.90")

		# Sender information
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec_minimum[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${direction}" "sender_rate" "${iteration}" $(bc -l <<< "scale=2; ${min_bps_tx}/1000000")
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec_maximum[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${direction}" "sender_rate" "${iteration}" $(bc -l <<< "scale=2; ${max_bps_tx}/1000000")
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec_average[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${direction}" "sender_rate" "${iteration}" $(bc -l <<< "scale=2; ${avg_bps_tx}/1000000")
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec_maximum_error[%d] %.2f%%\n" "${config_title}" "${iperf3_instances}" "${direction}" "sender_rate" "${iteration}" "${err_bps_tx}"
		# Sum of Mbps rates for all instances of iperf3 should be 
		# greater than 90% of expected throughput.
		if (( $(echo "${expected_throughput} > ${bps_tx_tot}" | bc -l) )); then
			printf "FAIL: average bitrate of %.2f Mbit/sec by is less than minimum threshold of %.2f Mbit/sec\n" $(bc -l <<< "scale=2; ${bps_tx_tot}/1000000") $(bc -l <<< "scale=2; ${expected_throughput}/1000000")
		else
			printf "bitrate of %.2f Mbit/sec is greater than minimum threshold of %.2f Mbit/sec\n" $(bc -l <<< "scale=2; ${bps_tx_tot}/1000000") $(bc -l <<< "scale=2; ${expected_throughput}/1000000")
			printf "%s\n" "PASS: test passes specified performance thresholds"
		fi
		
		# Receiver information
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec_minimum[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${direction}" "receiver_rate" "${iteration}" $(bc -l <<< "scale=2; ${min_bps_rx}/1000000")
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec_maximum[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${direction}" "receiver_rate" "${iteration}" $(bc -l <<< "scale=2; ${max_bps_rx}/1000000")
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec_average[%d] %.2f\n" "${config_title}" "${iperf3_instances}" "${direction}" "receiver_rate" "${iteration}" $(bc -l <<< "scale=2; ${avg_bps_rx}/1000000")
		printf "iperf3_%s_clients%d_%s_%s_mbit_per_sec_maximum_error[%d] %.2f%%\n" "${config_title}" "${iperf3_instances}" "${direction}" "receiver_rate" "${iteration}" "${err_bps_rx}"
		# Sum of Mbps rates for all instances of iperf3 should be 
		# greater than 90% of expected throughput.
		if (( $(echo "${expected_throughput} > ${bps_rx_tot}" | bc -l) )); then
			printf "FAIL: average bitrate of %.2f Mbit/sec by is less than minimum threshold of %.2f Mbit/sec\n" $(bc -l <<< "scale=2; ${bps_rx_tot}/1000000") $(bc -l <<< "scale=2; ${expected_throughput}/1000000")
		else
			printf "bitrate of %.2f Mbit/sec is greater than minimum threshold of %.2f Mbit/sec\n" $(bc -l <<< "scale=2; ${bps_rx_tot}/1000000") $(bc -l <<< "scale=2; ${expected_throughput}/1000000")
			printf "%s\n" "PASS: test passes specified performance thresholds"
		fi

		rm -f "${logfiles[@]}" || true
	done < <(jq -r 'keys[]' /tmp/iperf3-config.json)
}

for i in $(seq $test_iterations); do
	do_iteration $i
done
