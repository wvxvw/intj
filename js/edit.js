var cssUrl = document.location.href.replace(/\/[^\/]*$/g, '/css/');

var opts = {
    container: 'epiceditor',
    textarea: null,
    basePath: 'epiceditor',
    clientSideStorage: true,
    localStorageName: 'epiceditor',
    useNativeFullscreen: true,
    parser: marked,
    file: {
        name: 'epiceditor',
        defaultContent: '',
        autoSave: 100
    },
    theme: {
        base: cssUrl + 'epiceditor.css',
        preview: cssUrl + 'preview-dark.css',
        editor: cssUrl + 'epic-light.css'
    },
    button: {
        preview: true,
        fullscreen: true,
        bar: "auto"
    },
    focusOnLoad: false,
    shortcut: {
        modifier: 18,
        fullscreen: 70,
        preview: 80
    },
    string: {
        togglePreview: 'Toggle Preview Mode',
        toggleEdit: 'Toggle Edit Mode',
        toggleFullscreen: 'Enter Fullscreen'
    },
    autogrow: true
};

$(function () {
      var editor = new EpicEditor(opts), maxChars = 1024;
      editor.load();
      $('#post').on(
          'click', function () {
              $.ajax({ type: 'POST', url: '/post', data: editor.exportFile() })
                  .success(function (data) { document.location.href = '/profile'; })
                  .error(function (error) {
                             $("#notification").html(
                                 '<span class="label label-danger">' +
                                     'An error occured while posting your post: ' +
                                     JSON.stringify(error) + '</span>');
                         });
          });
      $('#profile').on('click', function () { document.location.href = '/profile'; });
      editor.on('update', function (event) {
                    var message = '', content = event.content;
                    if (content.length >= maxChars) {
                        message += '<span class="label label-danger">Extra characters: ' +
                            (content.length - maxChars) + '</span>';
                    } else {
                        message += '<span class="label label-info">Characters left: ' +
                            (maxChars - content.length) + '</span>';
                    }
                    if (/<|>/g.test(content)) {
                        message += '<br><span class="label label-warning">' +
                            '&lt; and &gt; will be ' +
                            ' converted to &amp;lt; and &amp;gt;</span>';
                    }
                    $("#notification").html(message);
                });
  });