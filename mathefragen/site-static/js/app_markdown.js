(function () {
    var converter = Markdown.getSanitizingConverter();
    converter.hooks.chain("preBlockGamut", function (text, rbg) {
        return text.replace(/^ {0,3}""" *\n((?:.*?\n)+?) {0,3}""" *$/gm, function (whole, inner) {
            return "<blockquote>" + rbg(inner) + "</blockquote>\n";
        });
    });
    var help = function () {
        window.open('http://stackoverflow.com/editing-help');
    };
    var editor = new Markdown.Editor(converter, null, {handler: help});

    var dialog = $('#insertImageDialog').dialog({
        autoOpen: false,
        closeOnEscape: false,
        position: {my: "center", at: "top 100", of: window},
        title: "Datei hinzufügen",
        open: function (event, ui) {
            $(".ui-dialog-titlebar-close").hide();
        }
    });

    var loader = $('span.image-loading-small', dialog);
    var url = $('input[type=text]', dialog);
    var file = $('input[type=file]', dialog);

    editor.hooks.set('insertImageDialog', function (callback) {
        // here we need to handle image upload on ourselves and then call the callback with image path
        // e.g. callback(image_path);

        // dialog functions
        var dialogInsertClick = function () {
            callback(url.val().length > 0 ? url.val() : null);
            dialogClose();
        };

        var dialogCancelClick = function () {
            dialogClose();
            callback(null);
        };

        var dialogClose = function () {
            // clean up inputs
            url.val('');
            file.val('');
            document.getElementById('insertImageDialog').classList.remove('hidden');
            dialog.dialog('close');
        };

        // set up dialog button handlers
        dialog.dialog('option', 'buttons', {
            'Einfügen': dialogInsertClick,
            'Abbrechen': dialogCancelClick
        });

        var uploadStart = function () {
            var loading_img = document.createElement('img');
            loading_img.src = loading_img_src;
            loading_img.setAttribute("style", "width: 40px");

            var consent_div = document.getElementsByClassName('ui-dialog-buttonset');
            var el = consent_div.item(0);
            el.innerHTML = '';

            var please_wait_txt = document.createTextNode('Bitte warten ...');
            el.appendChild(loading_img);
            el.appendChild(please_wait_txt);

            document.getElementById('insertImageDialog').classList.add('hidden');

        };

        var uploadComplete = function (response) {
            loader.hide();
            if (response === 'not_safe_for_work') {
                alert('Das Bild enthält unsicheren Inhalt.')
                dialogClose();
                return;
            }
            if ('response.success') {
                callback(response.location);
                dialogClose();
            } else {
                alert(response.message);
                file.val('');
            }
        };

        // upload
        file.unbind('change').ajaxfileupload({
            action: file.attr('data-action'),
            onStart: uploadStart,
            onComplete: uploadComplete
        });

        // open the dialog
        dialog.dialog('open');

        return true; // don't open default link dialog;
    });
    editor.run();
})();
