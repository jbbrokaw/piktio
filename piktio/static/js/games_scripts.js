/**
 * Created by jbbrokaw on 12/19/2014.
 */
var gameCollectionSource = $("#game-collection-template").html();
var gameSource = $("#game-template").html();
var userSource = $('#user-template').html();
var ratingSource = $('#rating-template').html();
var gameCollectionTemplate = Handlebars.compile(gameCollectionSource);
var gameTemplate = Handlebars.compile(gameSource);
var userTemplate = Handlebars.compile(userSource);
var ratingTemplate = Handlebars.compile(ratingSource);


var GameModel = Backbone.Model.extend({});

var GameCollection = Backbone.Collection.extend({
  group: 'all',
  urlBase: $('#url-root').val(),

  model: GameModel,

  url: function () {
    return this.urlBase + '/' + this.group;
  }
});

var UserModel = Backbone.Model.extend({
  defaults: {
    'csrf_token': $('#csrf').val(),
    'route': $('#follow-route').val()
  }
});

var RatingModel = Backbone.Model.extend({
  defaults: {
    'csrf_token': $('#csrf').val(),
    'route': $('#rate-route').val()
  }
});

var GameCollectionView = Backbone.View.extend({
  events: {
    'click #all-games': 'allGames',
    'click #my-games': 'myGames',
    'click #friends-games': 'friendsGames',
    'click .arrow-left.g-active': 'previousGame',
    'click .arrow-right.g-active': 'nextGame'
  },

  render: function () {
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
    $(this.el).html(gameTemplate(this.model.attributes));
    $('.game').empty().append(this.el);

    var subAuthView = new UserView({
      model: new UserModel(this.model.get('subject_author')),
      el: $('.subject')[0]
    });
    subAuthView.render();

    var predAuthView = new UserView({
      model: new UserModel(this.model.get('predicate_author')),
      el: $('.predicate')[0]
    });
    predAuthView.render();

    var firstDrawAuthView = new UserView({
      model: new UserModel(this.model.get('first_drawing_author')),
      el: $('.first_drawing')[0]
    });
    firstDrawAuthView.render();

    var firstDescAuthView = new UserView({
      model: new UserModel(this.model.get('first_description_author')),
      el: $('.first_description')[0]
    });
    firstDescAuthView.render();

    var secDrawAuthView = new UserView({
      model: new UserModel(this.model.get('second_drawing_author')),
      el: $('.second_drawing')[0]
    });
    secDrawAuthView.render();

    var secDescAuthView = new UserView({
      model: new UserModel(this.model.get('second_description_author')),
      el: $('.second_description')[0]
    });
    secDescAuthView.render();

    $('.rating-box').remove();
    $('<div class="rating-box"></div>').insertAfter('.game');
    var ratingView = new RatingView({
      model: new RatingModel(this.model.get('rating')),
      el: $('.rating-box')[0]
    });
    ratingView.render();

    app_router.navigate(String(this.model.get('id')));

    return this;
  }
});

var UserView = Backbone.View.extend({
  events: {
    'click .f-button': 'follow'
  },

  render: function () {
    $(this.el).empty().html(userTemplate(this.model.attributes));
    if (this.model.get('followed')) {
      $(this.el).children('p').children('.f-button').text('☑');
    } else {
      $(this.el).children('p').children('.f-button').text('☐');
    }
  },

  follow: function () {
    $.post(this.model.get('route'), this.model.attributes)
      .done(this.followDone(this))
      .fail(function (response) {
        console.log(response);
      });
  },

  followDone: function (view) {
    return function (server_response) {
      view.model.set(server_response);
      view.render();
    };
  }
});

var RatingView = Backbone.View.extend({
  events: {
    'click .rating > input': 'sendRating'
  },

  render: function () {
    $(this.el).empty().html(ratingTemplate(this.model.attributes));
    var rating = this.model.get('author_score');
    if (rating ===  null) {
      $('.rating input').prop('checked', false);
    } else {
      $selected = $('.rating input').eq(-rating);
      $selected.prop('checked', true);
    }
  },

  sendRating: function (event) {
    this.model.set('author_score', $(event.currentTarget).val());
    $.post(this.model.get('route'), this.model.attributes)
      .done(this.ratingDone(this))
      .fail(function (response) {
        console.log(response);
      });
  },

  ratingDone: function (view) {
    return function (server_response) {
      view.model.set(server_response);
      view.render();
    };
  }
});

var AppRouter = Backbone.Router.extend({
  routes: {
    ":id": "showGame",
    "*actions": "defaultRoute"
  },

  onCollectionLoad: function () {
    if (this.games.length === 0) {
      alert('No games in this category, reverting to all');
      this.mainView.allGames();
      return this;
    }
    this.games.selected = 0;
    this.games.trigger('selection');
  },

  onSelection: function () {
    if (this.games.selected <= 0) {
      $('.arrow-left').removeClass('g-active').addClass('g-inactive');
    } else {
      $('.arrow-left').removeClass('g-inactive').addClass('g-active');
    }
    if (this.games.selected >= (this.games.length - 1)) {
      $('.arrow-right').removeClass('g-active').addClass('g-inactive');
    } else {
      $('.arrow-right').removeClass('g-inactive').addClass('g-active');
    }
    if (typeof(this.subView) != 'undefined') {
      this.subView.remove();
    }
    this.subView = new GameView({
      model: this.games.models[this.games.selected]
    });
    if (this.subView.model.has('time_completed')) {
      this.subView.model.trigger('gotGame');
      //Go ahead and load old data, although followees might be out of date
    }
    this.subView.model.fetch({
      //Update data in all cases
      //(Maybe a flag could be set on follow/unfollow activity to indicate
      //when this is necessary)
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
  this.games.reset(initial);  // initial is provided in html
  this.games.trigger('load');
});

app_router.on('route:showGame', function (id) {
  if (typeof(this.games) === 'undefined') {
    this.games = new GameCollection();
    this.listenTo(this.games, "load", this.onCollectionLoad);
    this.listenTo(this.games, "selection", this.onSelection);
    this.games.reset(initial);  // initial is provided in html
  }
  if (typeof(this.mainView) === 'undefined') {
    this.mainView = new GameCollectionView({model: this.games});
    this.mainView.render();
  }
  id = parseInt(id);
  var chosenGame = this.games.findWhere({'id': id});
  var chosenIndex = this.games.models.indexOf(chosenGame);
  if (chosenIndex === -1) {
    // TODO: Maybe explain what happened to the user?
    console.log("Bad Game Index");
    chosenIndex = 0;
  }
  this.games.selected = chosenIndex;
  this.games.trigger('selection');
});

Backbone.history.start();
