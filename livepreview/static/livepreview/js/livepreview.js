$(document).ready(function() {

  // Whether or not the "autosave" function should be enabled.
  var updateLivePreview = true;
  // Check if on localhost. Used for console.log messages.
  var isLocalhost = false; //window.location.href.includes("localhost:")
  // Initial autosave serialized value
  var data_to_send = $("#page-edit-form").serialize()
  // Current number of autosaves.
  // When a certain number of autosaves are reached, this will
  // Automatically save a revision so the user doesn't accidentally lose their work.
  var autosaves = 1;
  // Every 1 second check if the live preview should be saving
  // This is just a wrapper for the actual event listener
  var livePreviewInterval = setInterval(function() {
    if(updateLivePreview) {
      $(".js-auto-save").trigger("click")
    }
  }, 1000);
  // Check if the content has changed at all.
  // This is used to change the iFrame src (just once)
  var contentHasChanged = false;

  /**
   * Setup the ajax calls to include the cookie
   */
  $.ajaxSetup({
    beforeSend: function beforeSend(xhr, settings) {
      function getCookie(name) {
        let cookieValue = null;

        if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');

          for (let i = 0; i < cookies.length; i += 1) {
            const cookie = jQuery.trim(cookies[i]);

            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (`${name}=`)) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }

        return cookieValue;
      }

      if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
        // Only send the token to relative URLs i.e. locally.
        xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
      }
    }
  })

  /**
   * Event listeners
   */
  $(document)
  .on("click", ".js-auto-save", function(e) {
    e.preventDefault()

    // The autosave button
    var $btn = $(this)
    // The default text in the autosave button
    // We use this to provide translation support through the JS
    var defaultBtnWording = $.trim($btn.text())
    var url = $btn.data("action")
    var data = $btn.closest("form").serialize()
    // If the values in the form haven't changed..
    // Don't send a save live preview request.
    if(data_to_send == data) {
      if(isLocalhost) {
        console.log("Localhost message:", "Stopping update because its the same")
      }
      return false;
    }
    // Data isn't the same as it was last time.
    // Make sure it's updated now to prevent this
    // event listener from running when it shouldn't.
    data_to_send = data;

    // Disable the button.
    $btn.prop("disabled", true).text($btn.data('saving-wording'))

    // Tthe official ajax request to the LivePreviewOnEdit view.
    $.ajax({
      url: url,
      type: 'POST',
      data: data,
      success: function (data, textStatus, jqXHR) {
          // Sometimes the response is too far and the button flickers too fast.
          // A 0.25s timeout to show "saved" with a checkmark.
          // Then a 0.5s timeout to revert back to normal
          setTimeout(function() {
            $btn.text($btn.data('saved-wording')).addClass("icon icon-tick")
            setTimeout(function() {
              $btn.prop("disabled", false).text(defaultBtnWording).removeClass("icon icon-tick")
            }, 500);
          }, 250);

          if(!contentHasChanged) {
            var $iframe = $("iframe.js-livepreview-iframe:first")
            var newIframeUrl = $iframe.attr('src').split("?from_revision")
            $iframe.attr('src', newIframeUrl[0] + '?from_live_preview=1')
            contentHasChanged = true;
          }

          // If the the page is supposed to save a revision every x number of livepreview saves
          // And the number of autosaves is at least as high as the LIVEPREVIEW_SAVE_REVISION_COUNT setting
          // The idea is to help prevent lost work in case users thing this is saving all their work (it's not)
          if(livepreviewSettings.auto_save_as_revision && autosaves >= livepreviewSettings.save_revision_count) {
            savePageRevision()
            // Reset the auto LivePreview save count.
            autosaves = 0
          }
          // Increment the autosaves every time this comes back successful
          autosaves++
      },
      error: function (xhr, result, errorThrown) {
        if(isLocalhost) console.error("Error", result)
        // Change the autosave button to an error button
        $btn.prop("disabled", true).addClass("no").addClass("icon icon-cross")
        var resetTime = 2500
        if (xhr.status === 404) {
          // Missing Ajax URL
          $btn.text($btn.data('404-wording'))
          console.error("Autosave failed due to missing page (404). Check to make sure Live Preview is finding the correct URL.")
          resetTime = 5000
        } else if (xhr.status === 403) {
          // Forbidden response. Probably missing a CSRF token or may not have proper permission.
          // Clear the interval so it stops running the autosave script.
          clearInterval(livePreviewInterval)
          $btn.text($btn.data('permission-denied-wording'))
          // User does not have permission to edit this page. No live preview will be available for them
          // Returning false will prevent the button from changing back.
          return false
        } else if (xhr.status === 400) {
          // A generally bad request was made.
          $btn.text($btn.data('error-wording'))
        } else {
          // Default error handler
          // Display a generic error message
          $btn.text($btn.data('error-wording'))
        }

        // Revert the button back after 2.5 seconds.
        setTimeout(function() {
          $btn.prop("disabled", false).text(defaultBtnWording).removeClass("no icon icon-cross")
        }, resetTime);
      }
    })
  })
  /**
   * Open and close the live preview pane in the admin.
   */
  .on("click", ".js-toggle-preview", function(e) {
    e.preventDefault()
    $(".js-preview-open:first").toggleClass("livepreview--closed")
    updateLivePreview = !updateLivePreview;
  })

  /**
   * Init Split.js for click-and-drag live preview pane ressizing
   * Don't init Split() if the two required ID's don't exist on the page.
   */
  if($("#livepreview-content").length && $("#livepreview-panel").length) {
    Split(['#livepreview-content', '#livepreview-panel']);
  }

  /**
   * Save a page revision.
   */
  function savePageRevision() {
    var $form = $("#page-edit-form")
    var url = $form.attr('action')
    var data = $form.serialize()
    $.ajax({
      url: url,
      type: 'POST',
      data: data,
      success: function (data, textStatus, jqXHR) {
        if(isLocalhost) console.log("Revision saved")
      },
      error: function (xhr, result, errorThrown) {
        if(isLocalhost)console.error("Revision save error", result)
      }
    })
  }
});
