(function() {
  var API_ENDPOINT, App, HTTP_SETTINGS, Home, Requests, Users, capitalize, router, toast,
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

  capitalize = function(str) {
    return _.capitalize(String(str));
  };

  API_ENDPOINT = 'https://api.frrand.com';

  HTTP_SETTINGS = {
    headers: {
      Authorization: 'JVJGBQEEOOGKVTSCHRXCIMJSZRGCNSAI',
      'Content-Type': 'application/json'
    }
  };

  Home = Vue.extend({
    template: '#home-template',
    http: HTTP_SETTINGS,
    data: function() {
      return {
        test: 'Hello World.',
        users: []
      };
    },
    methods: {
      dummyMethod: function() {
        return 'Hello world! ' + this.test;
      },
      getRequests: function() {
        this.$http.get(API_ENDPOINT + "/profiles", function(data, status, req) {
          if (status === 200) {
            return console.log(data);
          }
        });
      }
    },
    created: function() {
      console.log('Home is ready');
      return $(".sidebar").css('height', $(window).height());
    },
    ready: function() {
      return console.log('');
    }
  });

  Users = Vue.extend({
    template: '#users-template',
    http: HTTP_SETTINGS,
    data: function() {
      return {
        test: 'Hello World.',
        users: [],
        stats: {
          today: 0
        }
      };
    },
    methods: {
      patchUser: function(user) {
        var _data, _keys;
        _keys = ["username", "active", "points", "rating", "requestsDelivered", "requestsRecieved", "deviceType"];
        _data = _.pick(user, _keys);
        _data.active = _data.active === 'true' || _data.active === 'True';
        _data.rating = parseFloat(_data.rating);
        return this.$http.patch((API_ENDPOINT + "/adminUsers/") + user._id, _data, {
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
      calcUserStats: function() {
        var _date, _today, _user, j, len, ref, results;
        _today = moment().format('DDMMYYYY');
        ref = this.users;
        results = [];
        for (j = 0, len = ref.length; j < len; j++) {
          _user = ref[j];
          _date = moment(new Date(_user._created));
          if (_date.format('DDMMYYYY') === _today) {
            results.push(this.stats.today += 1);
          } else {
            results.push(void 0);
          }
        }
        return results;
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
              that.$http.get(API_ENDPOINT + "/adminUsers?max_results=500").then(function(resp) {
                var check, filterCheck, j, k, len, result;
                check = false;
                for (j = 0, len = filter.length; j < len; j++) {
                  k = filter[j];
                  if (!filter[k]) {
                    check = true;
                  }
                }
                filterCheck = function(obj) {
                  var l, len1;
                  for (l = 0, len1 = filter.length; l < len1; l++) {
                    k = filter[l];
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
              width: 100
            }, {
              name: 'active',
              title: 'Active',
              type: 'text',
              width: 50,
              align: 'center',
              "itemTemplate": function(val) {
                return capitalize(val);
              }
            }, {
              name: 'phone',
              title: 'Phone',
              type: "text",
              width: 110,
              align: 'center',
              editing: false
            }, {
              name: 'points',
              title: 'Points',
              type: "number",
              width: 60,
              align: 'center'
            }, {
              name: 'rating',
              title: 'Rating',
              type: "text",
              width: 60,
              align: 'center',
              itemTemplate: function(val) {
                return parseFloat(val).toFixed(2);
              }
            }, {
              name: 'requestsDelivered',
              title: 'Delivered',
              type: "number",
              width: 70,
              align: 'center'
            }, {
              name: 'requestsRecieved',
              title: 'Recieved',
              type: "number",
              width: 70,
              align: 'center'
            }, {
              name: 'deviceType',
              title: 'Platform',
              type: "text",
              width: 70,
              align: 'center'
            }, {
              name: '_created',
              title: 'Created',
              type: "text",
              width: 150,
              align: 'center',
              editing: false,
              "itemTemplate": function(val) {
                return moment(new Date(val)).format('ddd, MMM DD @ hh:mm A');
              },
              sorter: function(date1, date2) {
                return new Date(date1) - new Date(date2);
              }
            }, {
              type: 'control',
              width: 50
            }
          ],
          onItemUpdated: function(args) {
            if (that.patchUser(args.item)) {
              return true;
            } else {
              return false;
            }
          },
          onRefreshed: function(args) {
            var _height, _winHeight;
            _height = $("#users-table").height() + 20;
            _winHeight = $(window).height();
            _height = _height > _winHeight ? _height : _winHeight;
            return $('.sidebar').height(_height);
          }
        });
      }
    },
    created: function() {
      return console.log('ready');
    },
    ready: function() {
      console.log("Hello world!");
      this.initUserTable();
      return this.calcUserStats();
    }
  });

  Requests = Vue.extend({
    template: '#requests-template',
    http: HTTP_SETTINGS,
    data: function() {
      return {
        test: 'Hello World.',
        users: [],
        requests: [],
        addresses: [],
        map: {},
        mapOverlap: {},
        mapObjects: [],
        requestsCancelled: 0,
        requestsCompleted: 0,
        requestsPending: 0
      };
    },
    methods: {
      getUsers: function() {
        return this.$http.get(API_ENDPOINT + "/adminUsers?max_results=500").then(function(resp) {
          this.users = resp.data._items;
          return true;
        }, function(resp) {
          console.log("Failed to grab Users.");
          toast('Failed to grab Users from DB.', 5000, 'toast-negative');
          return false;
        });
      },
      getAddress: function(addr) {
        return this.$http.get(API_ENDPOINT + "/adminAddresses/" + addr).then(function(resp) {
          console.log(resp);
          return true;
        }, function(resp) {
          console.log(resp);
          return false;
        });
      },
      getAddresses: function() {
        return this.$http.get(API_ENDPOINT + "/adminAddresses").then(function(resp) {
          this.addresses = resp.data._items;
          return true;
        }, function(resp) {
          console.log(resp);
          return false;
        });
      },
      liveUpdateHandler: function() {
        console.log('Updating...');
        toast('Fetching data from DB');
        return $('#requests-table').jsGrid('loadData');
      },
      initMap: function() {
        var browserSupportFlag, handleNoGeolocation, iw, that, toronto;
        toronto = new google.maps.LatLng(43.6532, -79.3832);
        this.map = new google.maps.Map(document.getElementById("requests-map"), {
          zoom: 13
        });
        that = this;
        handleNoGeolocation = function(errorFlag) {
          var initialLocation;
          if (errorFlag === true) {
            initialLocation = toronto;
          } else {
            initialLocation = toronto;
          }
          that.map.setCenter(initialLocation);
        };
        if (navigator.geolocation) {
          browserSupportFlag = true;
          navigator.geolocation.getCurrentPosition((function(position) {
            var initialLocation;
            initialLocation = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
            that.map.setCenter(initialLocation);
          }), function() {
            handleNoGeolocation(browserSupportFlag);
          });
        } else {
          browserSupportFlag = false;
          handleNoGeolocation(browserSupportFlag);
        }
        this.mapOverlap = new OverlappingMarkerSpiderfier(this.map);
        iw = new google.maps.InfoWindow();
        google.maps.event.addListener(iw, 'closeclick', function() {
          console.log('Closed marker!');
          return this._path.setMap(null);
        });
        return this.mapOverlap.addListener('click', function(marker, event) {
          iw._path = new google.maps.Polyline({
            path: marker.routes,
            geodesic: true,
            strokeColor: '#00007f',
            strokeOpacity: 0.8,
            strokeWeight: 3
          });
          if (window._path) {
            window._path.setMap(null);
            window._path = iw._path;
          } else {
            window._path = iw._path;
          }
          iw._path.setMap(that.map);
          iw.setContent(marker.desc);
          return iw.open(that.map, marker);
        });
      },
      initMapMarkers: function(requests) {
        var LatLng, _cost, _destinationAddr, _destinationMarker, _destinationXY, _historyObj, _i, _items, _path, _pickupAddr, _pickupMarker, _pickupXY, _routes, _status, index, j, l, len, len1, ref, req, results, that, user;
        that = this;
        results = [];
        for (j = 0, len = requests.length; j < len; j++) {
          req = requests[j];
          if (req.cancel || req.complete) {
            continue;
          }
          _destinationAddr = _.find(this.addresses, {
            _id: req.destination
          });
          console.log(req.destination, this.addresses);
          if (!_destinationAddr) {
            this.getAddresses();
            _destinationAddr = _.find(that.addresses, {
              _id: req.destination
            });
            if (!_destinationAddr) {
              continue;
            }
          }
          _pickupAddr = req.places[0];
          user = this.findUser(req.createdBy);
          user = user ? user : {};
          _destinationXY = _destinationAddr.location.coordinates;
          _pickupXY = _pickupAddr.location.coordinates;
          _routes = [
            {
              lat: _pickupXY[1],
              lng: _pickupXY[0]
            }, {
              lat: _destinationXY[1],
              lng: _destinationXY[0]
            }
          ];
          _path = new google.maps.Polyline({
            path: _routes,
            geodesic: true,
            strokeColor: '#FF0000',
            strokeOpacity: 0.8,
            strokeWeight: 1
          });
          _pickupMarker = new google.maps.Marker({
            position: new google.maps.LatLng(_pickupXY[1], _pickupXY[0]),
            title: _pickupAddr.address,
            map: this.map,
            animation: google.maps.Animation.DROP,
            routes: _routes,
            icon: location.hostname === "localhost" ? '/assets/images/frrand-pickup-marker.png' : '/admin-panel/assets/images/frrand-pickup-marker.png'
          });
          LatLng = new google.maps.LatLng(_destinationXY[1], _destinationXY[0]);
          _destinationMarker = new google.maps.Marker({
            position: LatLng,
            title: _destinationAddr.address,
            routes: _routes,
            map: this.map,
            animation: google.maps.Animation.DROP,
            icon: location.hostname === "localhost" ? '/assets/images/frrand-marker.png' : '/admin-panel/assets/images/frrand-marker.png'
          });
          _items = "";
          _cost = 0;
          ref = req.items;
          for (index = l = 0, len1 = ref.length; l < len1; index = ++l) {
            _i = ref[index];
            _items += "<b>" + _i.quantity + "</b>x - <b>" + _i.name + "</b> for $" + (_i.price.toFixed(2));
            _items += index !== req.items.length - 1 ? '<br>' : '';
            _cost += parseFloat(_i.price);
          }
          _status = {};
          if (req.cancel) {
            _status["class"] = 'marker-negative';
            _status.status = 'Cancelled';
          } else if (req.complete) {
            _status["class"] = 'marker-positive';
            _status.status = 'Completed';
          } else if (req.pickedUp) {
            _status["class"] = 'marker-positive';
            _status.status = 'Picked Up';
          } else {
            _status["class"] = 'marker-warning';
            _status.status = 'Pending - waiting for pickup';
          }
          _destinationMarker.desc = "<span><b class=\"center\">" + user.username + " [" + (capitalize(_destinationAddr.name)) + "]</b></span><br>\n<span><em>" + user.phone + " - [" + (user.rating ? user.rating.toFixed(2) : 0) + "/5] - [" + user.points + " pts] </em></span><br>\n<span><b>To:</b> " + _destinationAddr.address + "</span><br>\n<span>" + (_destinationAddr.roomNumber ? "<b>Room:</b> " + String(_destinationAddr.roomNumber) + " - " : "") + " " + (_destinationAddr.buildingName ? "<b>Building:</b> " + _destinationAddr.buildingName + "<br>" : "") + " </span>\n<span><b>From:</b> " + _pickupAddr.address + "</span><br>\n<hr><span>" + _items + "</span><br>\n<hr>\n<span><b>Total: </b> $" + (_cost.toFixed(2)) + "</span><br>\n<span><b>Delivery Time:</b> " + (moment(new Date(req.requestedTime)).format('ddd, MMM MM @ hh:mm A')) + "</span><br>\n<span><b>Status:</b> <em class=\"" + _status["class"] + "\">" + _status.status + "</em> </span>";
          _pickupMarker.desc = "<b>" + _pickupAddr.address + "</b><br>\n<hr><span>" + _items + "</span><br>\n<hr>\n<span><b>Total: </b> $" + (_cost.toFixed(2)) + "</span><br>\n<span><b>Requester: </b> " + user.username + "</span><br>\n<span><b>Delivery Time:</b> " + (moment(new Date(req.requestedTime)).format('ddd, MMM MM @ hh:mm A')) + "</span><br>";
          _path.setMap(this.map);
          _historyObj = {
            _id: req._id,
            to: _destinationMarker,
            _from: _pickupMarker,
            path: _path,
            req: req
          };
          this.mapObjects.push(_historyObj);
          this.mapOverlap.addMarker(_destinationMarker);
          this.mapOverlap.addMarker(_pickupMarker);
          results.push(console.log('Plotting', _destinationAddr));
        }
        return results;
      },
      findUser: function(id) {
        var _user, that;
        _user = _.find(this.users, {
          '_id': id
        });
        that = this;
        if (!_user) {
          this.getUsers().then(function() {
            return _user = _.find(that.users, {
              '_id': id
            });
          });
        }
        return _user || null;
      },
      calcStats: function() {
        var cancelled, completed, pending;
        cancelled = _.filter(this.requests, {
          'cancel': true
        });
        completed = _.filter(this.requests, {
          'complete': true
        });
        pending = _.filter(this.requests, {
          'cancel': false,
          'complete': false
        });
        this.requestsCancelled = cancelled.length || 0;
        this.requestsCompleted = completed.length || 0;
        return this.requestsPending = pending.length || 0;
      },
      getRequests: function() {
        return this.$http.get(API_ENDPOINT + "/adminRequests").then(function(resp) {
          this.requests = resp.data._items;
          return true;
        }, function(resp) {
          console.log(resp);
          return false;
        });
      },
      initRequestsTable: function() {
        var that;
        that = this;
        return $('#requests-table').jsGrid({
          height: "auto",
          width: "100%",
          sorting: true,
          autoload: true,
          controller: {
            loadData: function(filter) {
              var d;
              d = $.Deferred();
              that.$http.get(API_ENDPOINT + "/adminRequests").then(function(resp) {
                var _find, _pending, _pendingObj, _toAdd, j, len, removeFromMap, result;
                result = resp.data._items;
                d.resolve(result);
                that.requests = result;
                that.calcStats();
                if (that.mapObjects.length !== 0) {
                  removeFromMap = function(obj) {
                    that.mapOverlap.removeMarker(obj.to);
                    that.mapOverlap.removeMarker(obj._from);
                    obj.to.setMap(null);
                    obj._from.setMap(null);
                    return obj.path.setMap(null);
                  };
                  _pending = _.filter(that.requests, {
                    'cancel': false,
                    'complete': false
                  });
                  _toAdd = [];
                  for (j = 0, len = _pending.length; j < len; j++) {
                    _pendingObj = _pending[j];
                    _find = _.find(that.mapObjects, {
                      _id: _pendingObj._id
                    });
                    if (_find) {
                      if (_.isEqual(_find.req, _pendingObj)) {
                        continue;
                      } else {
                        if (_pendingObj.cancel || _pendingObj.complete) {
                          removeFromMap(_find);
                        } else {
                          removeFromMap(_find);
                          _toAdd.push(_pendingObj);
                        }
                        _.remove(that.mapObjects, {
                          _id: _pendingObj._id
                        });
                      }
                    } else {
                      _toAdd.push(_pendingObj);
                    }
                  }
                  that.initMapMarkers(_toAdd);
                } else {
                  that.initMapMarkers(that.requests);
                }
                return true;
              }, function(resp) {
                console.log('failed');
                return false;
              });
              return d.promise();
            }
          },
          fields: [
            {
              name: 'createdBy',
              title: 'Username',
              type: "text",
              width: 100,
              editing: false,
              itemTemplate: function(val) {
                var _x;
                _x = that.findUser(val);
                if (_x) {
                  return _x.username;
                } else {
                  return 'Unknown';
                }
              }
            }, {
              name: 'cancel',
              title: 'Cancelled',
              type: "text",
              align: 'center',
              width: 80,
              "itemTemplate": function(val) {
                return capitalize(val);
              }
            }, {
              name: 'complete',
              title: 'Complete',
              type: "text",
              align: 'center',
              width: 80,
              "itemTemplate": function(val) {
                return capitalize(val);
              }
            }, {
              name: 'attachedInviteId',
              title: 'Attached',
              type: "text",
              align: 'center',
              width: 80,
              "itemTemplate": function(val) {
                if (val) {
                  return 'Yes';
                } else {
                  return 'No';
                }
              }
            }, {
              name: 'items',
              title: 'Items',
              type: "string",
              align: 'center',
              width: 80,
              itemTemplate: function(val) {
                var index, j, len, o, out;
                out = "";
                for (index = j = 0, len = val.length; j < len; index = ++j) {
                  o = val[index];
                  out += "<b>" + o.quantity + "</b>x - " + o.name + "</br>";
                }
                return out;
              }
            }, {
              name: 'items',
              title: 'Cost',
              type: "string",
              align: 'center',
              width: 80,
              itemTemplate: function(val) {
                var j, len, o, out;
                out = 0;
                for (j = 0, len = val.length; j < len; j++) {
                  o = val[j];
                  out += parseInt(o.price);
                }
                return "$" + (out.toFixed(2));
              },
              sorter: function(v1, v2) {
                var t;
                t = function(o) {
                  var _out, i, j, len;
                  _out = 0;
                  for (j = 0, len = o.length; j < len; j++) {
                    i = o[j];
                    _out += parseInt(i.price);
                  }
                  return _out;
                };
                return t(v1) - t(v2);
              }
            }, {
              name: '_created',
              title: 'Created',
              type: "text",
              width: 150,
              align: 'center',
              editing: false,
              "itemTemplate": function(val) {
                return moment(new Date(val)).format('ddd, MMM DD @ hh:mm A');
              },
              sorter: function(date1, date2) {
                return new Date(date1) - new Date(date2);
              }
            }, {
              name: 'requestedTime',
              title: 'Pickup',
              type: "text",
              width: 80,
              align: 'center',
              editing: false,
              "itemTemplate": function(val) {
                return moment(new Date(val)).format('hh:mm A');
              },
              sorter: function(date1, date2) {
                return new Date(date1) - new Date(date2);
              }
            }, {
              name: 'places',
              title: 'From:',
              type: "text",
              width: 150,
              align: 'center',
              itemTemplate: function(val) {
                return val[0].address;
              }
            }
          ],
          onRefreshed: function(args) {
            var _height, _winHeight;
            _height = $("#requests-table").height() + 600;
            _winHeight = $(window).height();
            _height = _height > _winHeight ? _height : _winHeight;
            return $('.sidebar').height(_height);
          },
          rowClick: function(args) {}
        });
      },
      testFn: function() {
        return this.getRequests();
      }
    },
    ready: function() {
      var that;
      that = this;
      console.log('[Requests Page] - Ready');
      return $(function() {
        return that.getUsers().then(function() {
          return that.getAddresses().then(function() {
            that.initMap();
            that.initRequestsTable();
            return window.liveUpdateTimer = setInterval(that.liveUpdateHandler, 30000);
          });
        });
      });
    },
    beforeDestroy: function() {
      return window.clearInterval(window.liveUpdateTimer);
    }
  });

  router = new VueRouter();

  router.map({
    '/': {
      component: Home
    },
    '/users': {
      component: Users
    },
    '/requests': {
      component: Requests
    }
  });

  App = Vue.extend({});

  router.start(App, '#app');

}).call(this);

