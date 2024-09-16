$(document).ready(function() {

    // Strip <script> tags from a string.
    function stripScripts(s) {
        var div = document.createElement('div');
        div.innerHTML = s;
        var scripts = div.querySelectorAll('.js-livepreview-script script');
        var i = scripts.length;
        while (i--) {
            scripts[i].parentNode.removeChild(scripts[i]);
        }
        return div.innerHTML;
    }

    // What is the current DOM as a string?
    window.currentDom = ''
    var totalRuns = 0;

    var livePreviewInterval = setInterval(() => {
        var bodyIsVisible = $("body").is(":visible")
        // If the body is not visible, don't try to update the dom.
        if(!bodyIsVisible) {
        	return false;
        }

        // Reload the page after 600 ajax requests
        // Should (hopefully) help with browsers lagging (or crashing)
        // if the page is left idle for too long.
        if(totalRuns === 600) {
            location.reload()
        }

        totalRuns++;

        $.ajax({
            url: livePreviewSettings.url,
            type: 'GET',
            success: function (data, textStatus, jqXHR) {
                if(window.currentDom !== data) {
                    window.currentDom = data
                    // Strip the ajax'd template data: no <scripts> allowed
                    data = stripScripts(data)
                    // Start a new DOMParser with the ajax'd template
                    // Note: Remember this ajax'd template has no <scripts> in it.
                    var parser = new DOMParser();
                    var htmlDoc = parser.parseFromString(data, 'text/html');
                    // Get only the <body> from the ajax'd template
                    var body = htmlDoc.querySelector('body')
                    // Replace our DOM with the Ajax'd DOM.
                    $("body").html(body.innerHTML)
                    // Update the page title now.
                    var title = htmlDoc.querySelector('title')
                    $("title").html(title.innerHTML)
                }
            },
            error: function (xhr, result, errorThrown) {
                console.error("Error", result)
                if (xhr.status === 404) {
                    // Missing Ajax URL
                    clearInterval(livePreviewInterval)
                } else if (xhr.status === 403) {
                    // Forbidden response. May not have proper permission.
                    clearInterval(livePreviewInterval)
                } else if (xhr.status === 400) {
                    clearInterval(livePreviewInterval)
                }
            }
        })
    }, livePreviewSettings.interval_time)
});
