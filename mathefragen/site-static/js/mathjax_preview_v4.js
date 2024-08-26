var Preview = {
    delay: 150,        // delay after keystroke before updating

    preview: null,     // filled in by Init below
    buffer: null,      // filled in by Init below
    textarea_id: null,      // filled in by Init below

    timeout: null,     // store setTimout id
    mjRunning: false,  // true when MathJax is processing
    mjPending: false,  // true when a typeset has been queued
    oldText: null,     // used to check if an update is needed

    // sometimes it can also render from simple textarea
    is_tiny_mce: true,

    //
    //  Get the preview and buffer DIV's
    //
    Init: function (textarea_id, preview_id, buffer_id, is_tiny_mce=true) {
        this.textarea_id = textarea_id;
        this.is_tiny_mce = is_tiny_mce;
        this.preview = document.getElementById(preview_id);
        this.buffer = document.getElementById(buffer_id);
    },

    //
    //  Switch the buffer and preview, and display the right one.
    //  (We use visibility:hidden rather than display:none since
    //  the results of running MathJax are more accurate that way.)
    //
    SwapBuffers: function () {
        var buffer = this.preview, preview = this.buffer;
        this.buffer = buffer;
        this.preview = preview;
        buffer.style.visibility = "hidden";
        buffer.style.position = "absolute";
        preview.style.position = "";
        preview.style.visibility = "";
    },

    //
    //  This gets called when a key is pressed in the textarea.
    //  We check if there is already a pending update and clear it if so.
    //  Then set up an update to occur after a small delay (so if more keys
    //    are pressed, the update won't occur until after there has been
    //    a pause in the typing).
    //  The callback function is set up below, after the Preview object is set up.
    //
    Update: function () {
        if (this.timeout) {
            clearTimeout(this.timeout)
        }
        this.timeout = setTimeout(this.callback, this.delay);
    },

    //
    //  Creates the preview and runs MathJax on it.
    //  If MathJax is already trying to render the code, return
    //  If the text hasn't changed, return
    //  Otherwise, indicate that MathJax is running, and start the
    //    typesetting.  After it is done, call PreviewDone.
    //
    CreatePreview: function () {
        Preview.timeout = null;
        if (this.mjPending) return;
        var text;
        if (this.is_tiny_mce) {
            text = tinymce.get(this.textarea_id).getContent();
        } else {
            text = document.getElementById(this.textarea_id).value;
            text = text.replace(/\n\r?/g, '<br/>');
        }
        if (text === this.oldtext) return;
        if (this.mjRunning) {
            this.mjPending = true;
            MathJax.Hub.Queue(["CreatePreview", this]);
        } else {
            this.buffer.innerHTML = this.oldtext = text;
            this.mjRunning = true;
            MathJax.Hub.Queue(
                ["Typeset", MathJax.Hub, this.buffer],
                ["PreviewDone", this]
            );
        }
    },

    //
    //  Indicate that MathJax is no longer running,
    //  and swap the buffers to show the results.
    //
    PreviewDone: function () {
        this.mjRunning = this.mjPending = false;
        this.SwapBuffers();
    }

};

//
//  Cache a callback to the CreatePreview action
//
Preview.callback = MathJax.Callback(["CreatePreview", Preview]);
Preview.callback.autoReset = true;  // make sure it can run more than once
