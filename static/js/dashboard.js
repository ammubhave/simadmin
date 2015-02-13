function post_to_get_response(endpoint, post_data) {
    var last_response_len = false;
    $.ajax(endpoint, {
        type: "POST",
        data: post_data,
        xhrFields: {
            onprogress: function(e)
            {
                var this_response, response = e.currentTarget.response;
                if(last_response_len === false)
                {
                    this_response = response;
                    last_response_len = response.length;
                }
                else
                {
                    this_response = response.substring(last_response_len);
                    last_response_len = response.length;
                }
                $('#status_window').append(this_response);
                //console.log(' onprocess');
            }
        }
    })
    .done(function(data)
    {   
        $('#status_window').append("\n============ DONE ============\nReload this page to see the changes.\n\n");
    })
    .fail(function(data)
    {
        $('#status_window').append("\n============ ERROR ============\n\n");
    });
    //console.log('Request Sent');
}

function _hide_all_website_types() {
    $('#new-website-type-group-static').hide();
}
function new_website_type_changed() {
    _hide_all_website_types();
    var type = $('#new-website-type').val();
    if (type == 'static') {
        $('#new-website-type-group-static').show();
    }
}

$(function () {
  $('[data-toggle="tooltip"]').tooltip();
});

