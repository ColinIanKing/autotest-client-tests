// Copyright (c) 2011 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// External Test Parameters Content Script!

// initial values.
var test_time_ms = 0;
var should_scroll = false;
var should_scroll_up = false;
var scroll_loop = false;
var scroll_interval_ms = 0;
var scroll_by_pixels = 0;
var tasks = "";

document.getElementById('myCustomEventDiv').addEventListener('myCustomEvent',
  function() {
    // pull our test parameters from divs on this page.
    var eventData = document.getElementById('myCustomEventDiv').innerText;
    test_time_ms = document.getElementById('test_time_ms').innerText;
    should_scroll = document.getElementById('should_scroll').innerText;
    should_scroll_up = document.getElementById('should_scroll_up').innerText;
    scroll_loop = document.getElementById('scroll_loop').innerText;
    scroll_interval_ms = document.getElementById('scroll_interval_ms').innerText;
    scroll_by_pixels = document.getElementById('scroll_by_pixels').innerText;
    tasks = document.getElementById('tasks').innerText;

    // pass to background page via sendRequest.
    var request = { _test_time_ms : test_time_ms,
                    _should_scroll : should_scroll,
                    _should_scroll_up : should_scroll_up,
                    _scroll_loop : scroll_loop,
                    _scroll_interval_ms : scroll_interval_ms,
                    _scroll_by_pixels : scroll_by_pixels,
                    _tasks : tasks
                  }
    chrome.extension.sendRequest(request);
  }
);

