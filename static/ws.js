// Copyright 2009 FriendFeed
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#addurl").click(function(){
        newMessage({"command":"addurl", "url":$("#url").val()});
        return false;
    });

    $("#next").click(function(){
        newMessage({"command":"next"});
        return false;
    });

    $("#url").select();
    updater.start();
});

function newMessage(message) {
    updater.socket.send(JSON.stringify(message));
}

var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/ws";
        if ("WebSocket" in window) {
	    updater.socket = new WebSocket(url);
        } else {
            updater.socket = new MozWebSocket(url);
        }
	updater.socket.onmessage = function(event) {

	}
    },
};