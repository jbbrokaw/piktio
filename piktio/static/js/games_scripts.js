/**
 * Created by jbbrokaw on 12/19/2014.
 */
var gameCollectionSource = $("#game-collection-template").html();
var gameSource = $("#game-template").html();
var gameCollectionTemplate = Handlebars.compile(gameCollectionSource);
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

var GameCollectionView = Backbone.View.extend({
  events: {
    'click #all-games': 'allGames',
    'click #my-games': 'myGames',
    'click #friends-games': 'friendsGames',
    'click .arrow-left': 'previousGame',
    'click .arrow-right': 'nextGame'
  },

  render: function () {
    console.log("Collection render");
    $(this.el).html(gameCollectionTemplate({}));
    $('#content').empty().append(this.el);
    return this;
  },

  allGames: function () {
    $('#all-games').addClass('g-selected')
      .siblings().removeClass('g-selected');
    this.model.group = "all";
    this.model.fetch({
      success: function (model, response, options) {
        model.trigger('load');
      }
    });
    return this;
  },

  myGames: function () {
    $('#my-games').addClass('g-selected')
      .siblings().removeClass('g-selected');
    this.model.group = "mine";
    this.model.fetch({
      success: function (model, response, options) {
        model.trigger('load');
      }
    });
    return this;
  },

  friendsGames: function () {
    $('#friends-games').addClass('g-selected')
      .siblings().removeClass('g-selected');
    this.model.group = "friends";
    this.model.fetch({
      success: function (model, response, options) {
        model.trigger('load');
      }
    });
    return this;
  },

  previousGame: function () {
    this.model.selected -= 1;
    this.model.trigger('selection');
  },

  nextGame: function () {
    this.model.selected += 1;
    this.model.trigger('selection');
  }
});

var GameView = Backbone.View.extend({
  initialize: function() {
    this.listenTo(this.model, "gotGame", this.render);
  },

  render: function () {
    console.log("Game render");
    $(this.el).html(gameTemplate(this.model.attributes));
    $('.game').empty().append(this.el);
    return this;
  }
});


var AppRouter = Backbone.Router.extend({
  routes: {
    "*actions": "defaultRoute"
  },

  onCollectionLoad: function () {
    if (this.games.length === 0) {
      alert('No games in this category, reverting to all');
      this.mainView.allGames();
      return this;
    }
    this.games.selected = 0;
    console.log("Triggering selection of 0");
    this.games.trigger('selection');
  },

  onSelection: function () {
    if (this.games.selected <= 0) {
      $('.arrow-left').hide();
    } else {
      $('.arrow-left').show();
    }
    if (this.games.selected >= (this.games.length - 1)) {
      $('.arrow-right').hide();
    } else {
      $('.arrow-right').show();
    }
    if (typeof(this.subView) != 'undefined') {
      this.subView.remove();
    }
    this.subView = new GameView({
      model: this.games.models[this.games.selected]
    });
    this.subView.model.fetch({
      success: function (model, response, options) {
        model.trigger('gotGame');
      }
    });
  }
});

var app_router = new AppRouter();

app_router.on('route:defaultRoute', function () {
  this.games = new GameCollection();
  this.mainView = new GameCollectionView({model: this.games});
  this.mainView.render();
  this.listenTo(this.games, "load", this.onCollectionLoad);
  this.listenTo(this.games, "selection", this.onSelection);
  this.games.fetch({
    success: function (model, response, options) {
      model.trigger('load');
    }
  });
});

Backbone.history.start();
