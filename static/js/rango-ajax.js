$(document).ready(function(){

    // JQuery code to be added here.

    // Like Button
    $('#likes').click(function(){
        var catid;
        catid=$(this).attr("data-catid");
        $.get('/rango/like_category/', {category_id: catid}, function(data){
            $('#like_count').html(data);
            $('#likes').hide();
            //$('#likes').css("visibility", "hidden").hide();
        });
    });

    // Dynamic category search suggestion
    $('#suggestion').keyup(function(){
        var query;
        query = $(this).val();
        $.get('/rango/suggest_category/', {suggestion: query }, function(data){
            $('#cats').html(data);
        });
    });

    // Add page button
    $('.rango-add').click(function(){
        var catid=$(this).attr("data-catid");
        var title=$(this).attr("data-title");
        var url=$(this).attr("data-url");
        var me = $(this);
        $.get('/rango/auto_add_page/', {category_id: catid, url: url, title: title }, function(data){
            $('#pages').html(data);
            me.hide();
        });
    });

});