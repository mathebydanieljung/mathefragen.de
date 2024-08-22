(function($) {

    'use strict';

    function initLeftMenuCollapse() {
        // Left menu collapse
        $('.button-menu-mobile').on('click', function (event) {
            event.preventDefault();
            $("body").toggleClass("enlarged");
        });
    }

    function init() {
        initLeftMenuCollapse();
    }
    init();

})(jQuery);


