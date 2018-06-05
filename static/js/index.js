$(function(){
    $page = jQuery.url.attr("file");
    if(!$page) {
        $page = 'index.html';
    }
    $('#navigation li a').each(function(){
        var $href = $(this).attr('href');
        if ( ($href == $page) || ($href == '') ) {
            $(this).addClass('on');
        } else {
            $(this).removeClass('on');
        }
    });
});