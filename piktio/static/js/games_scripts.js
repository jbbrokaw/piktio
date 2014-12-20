/**
 * Created by jbbrokaw on 12/19/2014.
 */
var gameSource = $("#game-template").html();
var gameTemplate = Handlebars.compile(gameSource);


var GameModel = Backbone.Model.extend({});

var GameCollection = Backbone.Collection.extend({
  group: 'all',
  urlBase: $('#url-root').val(),

  model: GameModel,

  url: function () {
    return this.urlBase + '/' + this.group;
  }
});

var GameView = Backbone.View.extend({
  initialize: function() {
    this.listenTo(this.model, "gotGame", this.render);
  },

  events: {
    'click #all-games': 'allGames',
    'click #my-games': 'myGames',
    'click #friends-games': 'friendsGames',
    'click #previous': 'previousGame',
    'click #next': 'nextGame'
  },

  render: function () {
    $('#content').empty();
    $(this.el).html(gameTemplate(this.model.toJSON()));
    $('#content').append(this.el);
    return this;
  },

  allGames: function () {
    this.model.collection.group = "all";
    this.model.collection.fetch();
    console.log("Set the collection to all & fetched");
    return;
  },

  myGames: function () {
    this.model.collection.group = "mine";
    this.model.collection.fetch();
    console.log("Set the collection to mine & fetched");
    return;
  },

  friendsGames: function () {
    this.model.collection.group = "friends";
    this.model.collection.fetch();
    console.log("Set the collection to friends & fetched");
    return;
  },

  previousGame: function () {
    console.log("Get previous game in collection");
  },

  nextGame: function () {
    console.log("Get next game in collection");
  }
});

var AppRouter = Backbone.Router.extend({
  routes: {
    "*actions": "defaultRoute"
  },

  onCollectionLoaded: function () {
    if (typeof(this.mainView) != 'undefined') {
      this.mainView.remove();
    }
    this.mainView = new GameView({model: this.games.first()});
    this.mainView.model.fetch({
      success: function (model, response, options) {
        model.trigger('gotGame');
      }
    });
  }
});

var app_router = new AppRouter();

app_router.on('route:defaultRoute', function () {
  this.games = new GameCollection();
  this.listenTo(this.games, "loaded", this.onCollectionLoaded);
  this.games.fetch({
    success: function (model, response, options) {
      model.trigger('loaded');
    }
  });
});

Backbone.history.start();
