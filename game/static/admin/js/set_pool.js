if (!$) {
    $ = django.jQuery;
}
function set_pool(pool_id, result) {
    $.post('/api/pools/' + pool_id + '/set/', {result:result}, function(success){
        console.log(success);
        location.reload();
    });
}
