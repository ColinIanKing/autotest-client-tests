import os
import helper
from autotest.client import test, utils


TEST_ITERATION = 3


class ubuntu_performance_deep_learning(test.test):
    version = 1

    def initialize(self):
        pass

    def install_required_pkgs(self):
        """
        Install required packages.

        This installation method assumes the corresponding GPU drivers are
        ready to load if the drivers are required by the deep learning
        framework. That being said, the installation will only install packages
        running in userspace, e.g. the framework itself and the corresponding
        runtime.
        """
        p_dir = os.path.dirname(os.path.abspath(__file__))
        uptf_cmd = os.path.join(p_dir, "ubuntu_performance_tensor_flow.sh")
        cmd = "{} setup".format(uptf_cmd)
        utils.system(cmd)

    def setup(self):
        self.install_required_pkgs()

    def tensor_flow_cnn_resnet(self, benchmark):
        """Test for running basic tensor flow features"""
        unit = "images/sec"
        max_error_threshold = 0.05
        values = {}

        # benchmark is the benchmark item of config.yaml
        benchmark = benchmark.replace("-", "_")
        if "TEST_CONFIG" in os.environ:
            benchmark += "_" + os.environ["TEST_CONFIG"]

        p_dir = os.path.dirname(os.path.abspath(__file__))
        uptf_cmd = os.path.join(p_dir, "ubuntu_performance_tensor_flow.sh")
        cmd = "{} test".format(uptf_cmd)

        for i in range(TEST_ITERATION):
            stdout_result = utils.system_output(cmd, retain_output=True)
            values[i] = helper.get_stats(stdout_result)

            if values[i]:
                print("")
                print("Test %d of %d:" % (i + 1, TEST_ITERATION))
                print("{}[{}] {} {}".format(benchmark, i, values[i], unit))

        #
        #  Compute min/max/average:
        #
        if values[i]:
            v = [float(values[i]) for i in values]
            maximum = max(v)
            minimum = min(v)
            average = sum(v) / float(len(v))
            max_err = (maximum - minimum) / average

            print("")
            print(benchmark + "_minimum {:.2f} {}".format(minimum, unit))
            print(benchmark + "_maximum {:.2f} {}".format(maximum, unit))
            print(benchmark + "_average {:.2f} {}".format(average, unit))
            print(benchmark + "_maximum_error {:.2%}".format(max_err))
            print("")

            if max_err > max_error_threshold:
                print("FAIL: maximum error is greater than 5%")
            else:
                print("PASS: test passes specified performance thresholds")
        else:
            print("NOT-RUN or FAIL to PARSE DATA")

    def run_once(self, test_name):
        if test_name == "tensor-flow-cnn-resnet":
            self.tensor_flow_cnn_resnet(test_name)

            print("")
            print("tensor_flow_cnn_resnet shell script has run.")

        print("")

    def postprocess_iteration(self):
        pass
