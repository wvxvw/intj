var cssUrl = document.location.href.replace(/\/[^\/]*$/g, '/css/');

var opts = {
    container           : 'epiceditor',
    textarea            : null,
    clientSideStorage   : true,
    localStorageName    : 'epiceditor',
    useNativeFullscreen : true,
    parser              : marked,
    autogrow            : true,
    file: {
        name: 'epiceditor',
        defaultContent: '',
        autoSave: 100
    },
    theme: {
        base    : cssUrl + 'epiceditor.css',
        preview : cssUrl + 'preview-dark.css',
        editor  : cssUrl + 'epic-light.css'
    },
    button: {
        preview    : true,
        fullscreen : true,
        bar        : "auto"
    },
    focusOnLoad: false,
    shortcut: {
        modifier   : 18,
        fullscreen : 70,
        preview    : 80
    },
    string: {
        togglePreview    : 'Toggle Preview Mode',
        toggleEdit       : 'Toggle Edit Mode',
        toggleFullscreen : 'Enter Fullscreen'
    }
};

var state = makeClass(
    function (app, container, tab) {
        this.app       = app;
        this.container = container;
        this.templates = [];
        this.handlers  = [];
        this.tab       = tab;
        tab.on('click', bind(
                   function () {
                       this.app.state.hide();
                       this.app.state = this;
                       this.render();
                   }, this));
    },
    {
        initialized : false,
        visible     : false,
        rendering   : false,
        templates   : null,
        handlers    : null,
        container   : null,
        tab         : null,
        
        render: function () {
            if (!this.rendering) {
                this.app.state = this;
                this.rendering = true;
                this.load(
                    bind(function (data) {
                             _.each(this.templates, funcall);
                             this.rendering = false;
                         }, this));
                this.show();
            } else if (!this.visible) this.show();
        },

        load: function (handler) {
            if (this.handlers.length) {
                _.reduce(
                    this.handlers.concat([null]), function (a, b) {
                        a.success =
                            bind(function (data) {
                                     console.log('loaded data ' + JSON.stringify(data));
                                     a.completed(data);
                                     if (b) {
                                         $.ajax({ url: b.url, data: b.contents, type: 'POST' })
                                             .success(function (data) { b.success(data); })
                                             .error(function (error) { b.error(error); });
                                     } else handler(data);
                                 }, a);
                        return b;
                    });
                $.ajax(this.handlers[0].url,
                       { contents: this.handlers[0].contents,
                         type: 'post' })
                    .success(this.handlers[0].success);    
            } else handler();
        },
        
        show: function () {
            this.container.removeClass("invisible");
            this.tab.addClass("active");
            this.visible = true;
        },
        
        hide: function () {
            this.container.addClass("invisible");
            this.tab.removeClass("active");
            this.visible = false;
        }
    }
);

var allFeeds = makeClass(
    function (app, container, tab) {
        var editor = new EpicEditor();
        this.callBase('constructor', [app, container, tab]);
        this.handlers.push(
        { url: '/feed/all',
          contents: { since: -1, limit: 10 },
          completed:
          bind(function (data) {
                   console.log('completed: ' + JSON.stringify(data.feeds));
                   // This should be a different template, actually
                   // the one which also has author-related info
                   _.each(data.feeds, function (feed) {
                              feed.text = editor.settings.parser(
                                  feed.text.replace('\\n', '\n'));
                          });
                   this.feedData.feeds = data.feeds;
                   this.feedData.title = 'All Feeds';
               }, this)
        });
        this.templates.push(
            bind(function (tpl, data) {
                     return function () {
                         if (!this.initialized) {
                             console.log('rednering: ' + JSON.stringify(data.feeds));
                             console.log('title: ' + data.title);
                             this.container.html(tpl(data));
                             this.initialized = true;
                         }
                     };
                 }(_.template($("#all-feeds-tpl").val()), this.feedData),
                 this)
        );
    },
    { feedData: { feeds: [],
                  title: 'No Data Recieved',
                  id: 'all-feeds' }
    }, null, state
);

var myFeed = makeClass(
    function (app, container, tab) {
        var editor = new EpicEditor();
        this.callBase('constructor', [app, container, tab]);
        this.handlers.push(
        { url: '/feed/me',
          contents: { since: -1, limit: 10 },
          completed:
          bind(function (data) {
                   console.log('completed: ' + JSON.stringify(data.feeds));
                   _.each(data.feeds, function (feed) {
                              feed.text = editor.settings.parser(
                                  feed.text.replace('\\n', '\n'));
                          });
                   this.feedData.feeds = data.feeds;
                   this.feedData.title = 'My Feed';
               }, this)
        });
        this.templates.push(
            bind(function (tpl, data) {
                     return function () {
                         if (!this.initialized) {
                             console.log('rednering: ' + JSON.stringify(data.feeds));
                             console.log('title: ' + data.title);
                             this.container.html(tpl(data));
                             this.initialized = true;
                         }
                     };
                 }(_.template($("#feeds-tpl").val()), this.feedData),
                 this)
        );
    },
    { feedData: { feeds: [],
                  title: 'No Data Recieved',
                  id: 'my-feed' }
    }, null, state
);

var myProfile = makeClass(
    function (app, container, tab) {
        this.callBase('constructor', [app, container, tab]);
        this.handlers.push(
        { url: '/profile/me',
          completed:
          bind(function (data) {
                   console.log('Profile loaded: ' +
                               JSON.stringify(data.user.name));
                   this.profileData.user.name = data.user.name;
                   this.profileData.user.id = data.user.id;
                   this.profileData.followed = data.followed;
                   this.profileData.followers = data.followers;
               }, this)
        });
        this.templates.push(
            bind(function (tpl, data) {
                     return function () {
                         if (!this.initialized) {
                             console.log('allFeeds rendered: ' +
                                         JSON.stringify(new Error('feeds').stack));
                             this.container.html(tpl(data));
                             this.initialized = true;
                         }
                     };
                 }(_.template($("#profile-tpl").val()), this.profileData), this)
        );
    },
    { profileData: { user: { name: "Me", id: NaN },
                     followedId: 'people-i-follow',
                     followersId: 'people-following-me' }
    } , null, state
);

var nextPost = makeClass(
    function (app, container, tab) {
        var editor = new EpicEditor(opts), maxChars = 1024;
        this.callBase('constructor', [app, container, tab]);
        function resetEditor() {
            editor.remove("intj-post-template.md");
            editor.open("intj-post-template.md");
        }
        this.templates.push(
            bind(function (data) {
                     editor.load();
                     editor.open("intj-post-template.md");
                     $('#post').on(
                         'click', function () {
                             $.ajax({ type: 'POST', url: '/post', data: editor.exportFile() })
                                 .success(resetEditor)
                                 .error(function (error) {
                                            $("#notification").html(
                                                '<span class="label label-danger">' +
                                                    'An error occured while posting your post: ' +
                                                    JSON.stringify(error) + '</span>');
                                        });
                         });
                     $('#clear').on('click', resetEditor);
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
                 }));
    }, null, null, state
);

var application = makeClass(
    function (container) {
        this.container = container;
        this.states =
            { myProfile : new myProfile(
                  this, $("#my-profile-view"), $("#my-profile-tab")),
              allFeeds  : new allFeeds(
                  this, $("#all-feeds-view"), $("#all-feeds-tab")),
              myFeed    : new myFeed(
                  this, $("#my-feeds-view"), $("#my-feeds-tab")),
              nextPost  : new nextPost(
                  this, $("#post-editor"), $("#next-post-tab")) };
    },
    { state: null,
      states: null,
      container: null,
      init: function () {
          this.states.nextPost.render();
      }
    }
);

$(function () { new application($("#container")).init(); });