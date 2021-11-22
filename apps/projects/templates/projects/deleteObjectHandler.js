function deleteObjectHandler(className, msg) {
    $(`.${className}`).click(function (event) {
        event.preventDefault();
        let url = $(this).data('delete-url');
        if (confirm(msg) && url) {
            window.location.replace(url);
        }
    });
}