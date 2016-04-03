(function() {
  var App, Home, Users, router, toast,
    indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  toast = function(msg, duration, warn) {
    if (duration == null) {
      duration = 2000;
    }
    if (warn == null) {
      warn = 'toast-neutral';
    }
    return Materialize.toast(msg, duration, warn);
  };

  Home = Vue.extend({
    template: '#home-template',
    http: {
      headers: {
        Authorization: 'IBJKYFHFFZLCZHVDSYZFWABYAJWSJECM'
      }
    },
    data: {
      test: 'Hello World.',
      users: []
    },
    methods: {
      dummyMethod: function() {
        return 'Hello world! ' + this.test;
      },
      getRequests: function() {
        this.$http.get('https://dev-api.frrand.com/profiles', function(data, status, req) {
          if (status === 200) {
            return console.log(data);
          }
        });
      }
    },
    created: function() {
      return console.log('Home is ready');
    },
    ready: function() {
      return console.log("Hello world!");
    }
  });

  Users = Vue.extend({
    template: '#users-template',
    http: {
      headers: {
        Authorization: 'IBJKYFHFFZLCZHVDSYZFWABYAJWSJECM',
        'Content-Type': 'application/json'
      }
    },
    data: {
      test: 'Hello World.',
      users: []
    },
    methods: {
      patchUser: function(user) {
        var _data, _keys;
        _keys = ["username", "active", "phone", "points", "rating", "requestsDelivered", "requestsRecieved", "deviceType"];
        _data = _.pick(user, _keys);
        _data.active = _data.active === 'true';
        return this.$http.patch('https://dev-api.frrand.com/adminUsers/' + user._id, _data, {
          'headers': {
            'If-Match': user._etag
          }
        }).then(function(resp) {
          console.log(resp);
          toast("Succesfully patched [" + user.username + "].", 2000, 'toast-positive');
          return true;
        }, function(resp) {
          console.log('error', resp);
          toast("Failed to patch [" + user.username + "]!", 2000, 'toast-negative');
          return false;
        });
      },
      initUserTable: function() {
        var that;
        that = this;
        return $('#users-table').jsGrid({
          height: "auto",
          width: "100%",
          editing: true,
          sorting: true,
          autoload: true,
          controller: {
            loadData: function(filter) {
              var d;
              d = $.Deferred();
              that.$http.get('https://dev-api.frrand.com/adminUsers').then(function(resp) {
                var check, filterCheck, i, k, len, result;
                check = false;
                for (i = 0, len = filter.length; i < len; i++) {
                  k = filter[i];
                  if (!filter[k]) {
                    check = true;
                  }
                }
                filterCheck = function(obj) {
                  var j, len1;
                  for (j = 0, len1 = filter.length; j < len1; j++) {
                    k = filter[j];
                    if (indexOf.call(obj, k) >= 0 && obj[k] === filter[k]) {
                      return true;
                    }
                  }
                  return false;
                };
                result = resp.data._items;
                if (check) {
                  console.log('Checking against our filter');
                  result = result.filter(filterCheck);
                }
                d.resolve(result);
                console.log(result);
                return that.users = result;
              }, function(resp) {
                console.log('failed');
                return 0;
              });
              return d.promise();
            }
          },
          fields: [
            {
              name: 'username',
              title: 'Username',
              type: "text",
              width: 50
            }, {
              name: 'active',
              title: 'Active',
              type: 'text',
              width: 20,
              align: 'center',
              "itemTemplate": function(val) {
                return _.capitalize(String(val));
              }
            }, {
              name: 'phone',
              title: 'Phone',
              type: "text",
              width: 45,
              align: 'center'
            }, {
              name: 'points',
              title: 'Points',
              type: "number",
              width: 20,
              align: 'center'
            }, {
              name: 'rating',
              title: 'Rating',
              type: "number",
              width: 10,
              align: 'center'
            }, {
              name: 'requestsDelivered',
              title: 'Delivered',
              type: "number",
              width: 20,
              align: 'center'
            }, {
              name: 'requestsRecieved',
              title: 'Recieved',
              type: "number",
              width: 20,
              align: 'center'
            }, {
              name: 'deviceType',
              title: 'Platform',
              type: "text",
              width: 35,
              align: 'center'
            }, {
              name: '_created',
              title: 'Created',
              type: "text",
              width: 50,
              align: 'center',
              editing: false,
              "itemTemplate": function(val) {
                return val.slice(0, -4);
              }
            }, {
              type: 'control',
              width: 10
            }
          ],
          onItemUpdated: function(args) {
            return that.patchUser(args.item);
          }
        });
      }
    },
    created: function() {
      return console.log('ready');
    },
    ready: function() {
      console.log("Hello world!");
      return this.initUserTable();
    }
  });

  router = new VueRouter();

  router.map({
    '/': {
      component: Home
    },
    '/users': {
      component: Users
    }
  });

  App = Vue.extend({});

  router.start(App, '#app');

}).call(this);

