var inherit = function (d, b) {
    function __() { this.constructor = d; }
    __.prototype = b.prototype;
    d.prototype = new __();
    return d;
};

var bind = function (f, o) {
    return function () { return f.apply(o, arguments); };
};

var makeClass = function (constructor, fields, statics, base) {
    var result = inherit(constructor, base || Object), p;
    _.each(fields, function (value, key) { result.prototype[key] = value; });
    _.each(statics, function (value, key) { result[key] = value; });
    if (base) result.prototype.base = base.prototype;
    result.prototype.self = result;
    result.prototype.callBase = function (func, args) {
        base.prototype[func].apply(this, args);
    };
    return result;
};

var funcall = function (f) { return f(); };

var state = makeClass(
    function (app) {
        this._app = app;
        this.container = app.container;
        this.templates = [];
        this.handlers = [];
    },
    {
        initialized: false,
        visible: false,
        rendering: false,
        templates: null,
        handlers: null,
        container: null,
        
        render: function () {
            if (!this.rendering) {
                this._app.state = this;
                this.rendering = true;
                this.load(
                    bind(function (data) {
                             _.each(this.templates, funcall);
                             this.rendering = false;
                         }, this));
            } else if (!this.visible) this.show();
        },

        load: function (handler) {
            _.reduce(
                this.handlers.concat([null]), function (a, b) {
                    a.success =
                        bind(function (data) {
                                 console.log('loaded data ' + JSON.stringify(data));
                                 a.completed(data);
                                 if (b) {
                                     $.ajax(b.url, { contents: b.contents, type: 'post' })
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
        },
        
        show: function () {
            this.visible = true;
        },
        
        hide: function () {
            this.visible = false;
        }
    }
);

var allFeedsState = makeClass(
    function (app) {
        this.callBase('constructor', [app]);
        this.templates.push(
            bind(function () {
                     var tpl = _.template($("#feeds-tpl").val()),
                     data = { feeds: [],
                              title: 'No Data Recieved',
                              id: 'all-feeds-list' };
                     return function () {
                         if (!this.initialized) {
                             console.log('allFeeds rendered: ' + JSON.stringify(new Error('feeds').stack));
                             this.container.html(tpl(data));
                             this.initialized = true;
                         }
                     };
                 }(), this)
        );
    }, null, null, state
);

var myProfile = makeClass(
    function (app) {
        this.callBase('constructor', [app]);
        this.handlers.push(
        { url: '/feed/me',
          contents: { since: -1, limit: 10 },
          completed:
          bind(function (data) {
                   console.log('completed: ' + JSON.stringify(data.feeds));
                   this.feedData.feeds = data.feeds;
                   this.feedData.title = 'My Feeds';
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

var application = makeClass(
    function (container) {
        this.container = container;
        this.states = { myProfile: new myProfile(this),
                        allFeeds: new allFeedsState(this) };
    },
    { state: null,
      states: null,
      container: null,
      init: function () {
          this.states.myProfile.render();
      }
    }
);

$(function () { new application($("#container")).init(); });