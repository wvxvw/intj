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