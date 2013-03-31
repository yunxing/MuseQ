String.prototype.format = function (){var d=this.toString();if(!arguments.length)return d;var a="string"==typeof arguments[0]?arguments:arguments[0],c;for(c in a)d=d.replace(RegExp("\\{"+c+"\\}","gi"),a[c]);return d};


function Table_creator() {
    var html = ""
    var body_id=""
    this.init = function(){
        html = "<table class='search table table-condensed'>";
        html += "<thead><tr>";
        for (var i=0; i < arguments.length; i++) {
            html += '<th>' + arguments[i] + '</th>\n';
        }
        html += "</tr></thead>";
        html += "<tbody>"
    }

    this.insert_row = function(str) {
        html += str;
    };

    this.finish = function() {
        return html + "</tbody></table>";
    };
};



function Search_modal(div_id) {
    var div_id = div_id;
    var init_tab = function(tab_id){
        $('#' + tab_id).html("<p>Loading query result...</p>");
    };
    this.init = function() {
        $('#' + div_id).modal();
        init_tab("song-tab");
        init_tab("album-tab");
    };

    var create_song_table = function(result){
        var song_table = new Table_creator();
        song_table.init("Title", "Artist", "Album");
        result.forEach(function(song, index) {
            row_str = "<tr id='song-result" + index + "'> \
              <td>" + song.title + "</td> \
              <td>" + song.artist + "</td> \
              <td>" + song.album + "</td> \
            </tr>\n";
            song_table.insert_row(row_str);
        });
        $("#song-tab").html(song_table.finish());

        result.forEach(function(song, index) {
            $("#song-result" + index).click(function(){
                newMessage({"command":"addurl", "url":song.url});
                $('#search-modal').modal('hide');
            });
        });
    }

    var create_album_table = function(result){
        var album_table = new Table_creator();
        album_table.init("Title", "Artist");
        result.forEach(function(album, index) {
            row_str = "<tr id='album-result" + index + "'> \
              <td>" + album.title + "</td> \
              <td>" + album.artist + "</td> \
            </tr>\n";
            album_table.insert_row(row_str);
        });
        $("#album-tab").html(album_table.finish());

        result.forEach(function(album, index) {
            $("#album-result" + index).click(function(){
                newMessage({"command":"addurl", "url":album.url});
                $('#search-modal').modal('hide');
            });
        });
    }

    this.update = function(result) {
        create_song_table(result.songs);
        create_album_table(result.albums);
    }
};

var search_modal = new Search_modal("search-modal")

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    // $("#addurl").click(function(){
    //     newMessage({"command":"addurl", "url":$("#url").val()});
    //     return false;
    // });

    // $("#url").keypress(function(event) {
    //     if ( event.which == 13 ) {
    //         newMessage({"command":"addurl", "url":$("#url").val()});
    //     }
    // });

    $("#addurl").click(function(){
        search_modal.init();
        newMessage({"command":"search", "query":$("#url").val()});
        return false;
    });

    $("#url").keypress(function(event) {
        if ( event.which == 13 ) {
            search_modal.init();
            newMessage({"command":"search", "query":$("#url").val()});
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
        class_str = (item.playing) ? "class='success'" : "";

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

function result_got(result) {
    search_modal.update(result);
}

var dispathcer = {
    "update": update_playlist,
    "toggle": update_playstatus,
    "result": result_got,
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
