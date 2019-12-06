function chatBot(){

    query=$("#query_text").val();
    $("#query_text").val('');
    window.console.log(query)
    entry={"query":query};

    var ele='<div class="outgoing-chats">'+
                '<div class="outgoing-msg">'+
                    '<div class="outgoing-msg-inbox">'+
                    '<p>'+query+'</p>'+     
                    '<span class="outgoing-time">11:03 PM | October 11</span>'+
                    '</div>'+
                '</div>'+
                '<div class="outgoing-chats-img">'+
                        '<i class="fa fa-user user-img"></i>'+
                '</div></div>'

    

    window.console.log(ele)
    $('#chat_page').append(ele)



    fetch(`${window.origin}/chatBot`,{
        method:"POST",
        credentials:"include",
        body: JSON.stringify(entry),
        cache:"no-cache",
        headers:new Headers({
        "content-type":"application/json"
        })  
        })
        .then(function (response){  
            if(response.status !=200){
                console.log(`Response status was not 200: ${response.status}`);
                return;

            }
            response.json().then(function(data){
                intent=data["intent"]
                var bot_ele='<div class="recieved-chats">'+
                    '<div class="recieved-chats-img">'+
                            '<i class="fa fa-slideshare bot-img" ></i>'+     
                    '</div><div class="recieved-msg">'+
                        '<div class="recieved-msg-inbox">'+
                        '<p> Your intent is '+intent+'</p>'+
                        '<span class="recieved-time">11:01 PM | October 11</span>'+
                        '</div></div></div>'
                $('#chat_page').append(bot_ele)
                console.log(data)
                
            }
            )

        })

}