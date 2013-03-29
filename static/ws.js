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

String.prototype.format = function (){var d=this.toString();if(!arguments.length)return d;var a="string"==typeof arguments[0]?arguments:arguments[0],c;for(c in a)d=d.replace(RegExp("\\{"+c+"\\}","gi"),a[c]);return d};

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#addurl").click(function(){
        newMessage({"command":"addurl", "url":$("#url").val()});
        return false;
    });

    $("#url").keypress(function(event) {
        if ( event.which == 13 ) {
            newMessage({"command":"addurl", "url":$("#url").val()});
        }
    });

    $("#next").click(function(){
        newMessage({"command":"next"});
        return false;
    });

    $("#toggle").click(function(){
        newMessage({"command":"toggle"});
        return false;
    });

    $("#volumeup").click(function(){
        newMessage({"command":"volumeup"});
        return false;
    });

    $("#volumedown").click(function(){
        newMessage({"command":"volumedown"});
        return false;
    });

    $("#stop").click(function(){
        newMessage({"command":"stop"});
        return false;
    });

    $("#url").select();
    updater.start();
});

function newMessage(message) {
    updater.socket.send(JSON.stringify(message));
}

function update_playlist(playlist) {
    $("#playlist").html("");
    playlist.forEach(function(item){
        class_str = (item.playing)? "class='success'" : "";

        item_str = "<tr {0} id='song{1}'> \
          <td>{1}</td> \
          <td>{2}</td> \
          <td>{3}</td> \
          <td>{4}</td> \
        </tr>".format(class_str,
                      item.id,
                      item.title,
                      item.artist,
                      item.album);
        $("#playlist").append(item_str);
        $("#song" + item.id).click(function(){
            newMessage({"command":"select", "id":item.id});
        });
    });

};

function update_playstatus(status) {
    if (status == "play"){
        $("#toggle-icon").attr('class', 'icon-pause');
    } else {
        $("#toggle-icon").attr('class', 'icon-play');
    }
};

var dispathcer = {
    "update": update_playlist,
    "toggle": update_playstatus,
};

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
            msg = JSON.parse(event.data)
            console.log("Got msg:")
            console.log(msg)
            dispathcer[msg.command](msg.arg)

	}
    },
};
