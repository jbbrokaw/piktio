/**
 * Created by jbbrokaw on 12/12/2014.
 */
var textEntrySource   = $("#text-entry-template").html();
var textEntryTemplate = Handlebars.compile(textEntrySource);
var userSource = $('#user-template').html();
var drawingSource = $("#drawing-template").html();
var drawingTemplate = Handlebars.compile(drawingSource);
var userTemplate = Handlebars.compile(userSource);


var StepModel = Backbone.Model.extend({
  defaults: {
    'csrf_token': $('#csrf').val(),
    'route': $('#route').val()
  }
});

var UserModel = Backbone.Model.extend({
  defaults: {
    'csrf_token': $('#csrf').val(),
    'route': $('#follow-route').val()
  }
});


var TextEntryView = Backbone.View.extend({

  events: {
    'click .t-button': 'submitText'
  },

  render: function () {
    $('#content').empty();
    $(this.el).html(textEntryTemplate(this.model.toJSON()));
    $('#content').append(this.el);
    _.each(this.model.get('authors'), function (author) {
      aView = new UserView({
        model: new UserModel(author)
      });
      aView.render();
      $('.prev-auth-list').append(aView.el);
    });
    return this;
  },

  next_step: function (view) {
    return function (server_response) {
      if (typeof(server_response.error) !== 'undefined') {
        alert(server_response.error);
        return;
      }
      if (typeof(server_response.redirect) !== 'undefined') {
        window.open(server_response.redirect, '_self');
      }
      view.model.clear().set(server_response);
      if (server_response.route.search('predicate') > -1) {
        view.render();
        view.delegateEvents();
        return;
      }
      view.remove();
      view = new DrawingView({model: view.model});
      view.render();
      app_router.mainView = view;
    };
  },

  submitText: function () {
    if ($('#prompt-entry').val() === "") {
      alert("You have to type something in the entry box");
      return;
    }
    //this.model.set('prompt', $('#prompt-entry').val());
    //var payload = this.model.toJSON();
    var payload = {'prompt': $('#prompt-entry').val(),
                   'game_id': this.model.get('game_id'),
                   'csrf_token': this.model.get('csrf_token')};
    $.post(this.model.get('route'), payload)
      .done(this.next_step(this))
      .fail(function (response) {
        console.log(response);
    });
  }
});

var DrawingView = Backbone.View.extend({

  events: {
    'click #upload': 'submitDrawing',
    'click .color-selectors li': 'setColor',
    'click .size-selectors .sizer': 'setSize',
    'click #undo': 'undo',
    'click #clear': 'clear',
    'click #toggle-controls': 'toggleFreeDraw'
    //'click #redo': 'redo'
  },

  render: function () {
    $('#content').empty();
    $(this.el).html(drawingTemplate(this.model.toJSON()));
    $('#content').append(this.el);

    this.drawingCanvas = new fabric.Canvas('drawing', {
      isDrawingMode: true
    });
    this.drawingCanvas.setHeight(320);
    this.drawingCanvas.setWidth(320);
    fabric.Object.prototype.transparentCorners = false;
    this.drawingCanvas.freeDrawingBrush.width = 30;
    //this.drawingCanvas.redostack = new Array();

    _.each(this.model.get('authors'), function (author) {
      aView = new UserView({
        model: new UserModel(author)
      });
      aView.render();
      $('.prev-auth-list').append(aView.el);
    });

    return this;
  },

  next_step: function (view) {
    return function (server_response) {
      if (typeof(server_response.error) !== 'undefined') {
        alert(server_response.error);
        return;
      }
      view.model.clear().set(server_response);
      view.remove();
      view = new TextEntryView({model: view.model});
      view.render();
      app_router.mainView = view;
    };
  },

  setColor: function (event) {
    $element = $(event.currentTarget);
    this.drawingCanvas.freeDrawingBrush.color = $element.css('background-color');
    $element.siblings().removeClass('selected');
    $element.addClass('selected');
  },

  setSize: function (event) {
    $sizeElement = $(event.currentTarget).children().first();
    this.drawingCanvas.freeDrawingBrush.width = Number($sizeElement.css('height').slice(0, -2));
    $('.sizer .selector').removeClass('selected');
    $sizeElement.addClass('selected');
  },

  undo: function () {
    this.drawingCanvas.remove(
      this.drawingCanvas.getObjects().pop()
    );
  },

  clear: function () {
    this.drawingCanvas.clear();
  },

  submitDrawing: function () {
    if (this.drawingCanvas.getObjects().length === 0) {
      alert("Do not submit a blank canvas");
      return;
    }
    //this.model.set('drawing', this.drawingCanvas.toDataURL('png'));
    //var payload = this.model.toJSON();
    var payload = {'drawing': this.drawingCanvas.toDataURL('png'),
                   'game_id': this.model.get('game_id'),
                   'csrf_token': this.model.get('csrf_token')};
    this.drawingCanvas.dispose();
    $.post(this.model.get('route'), payload)
      .done(this.next_step(this))
      .fail(function (response) {
        console.log(response);
    });
  },

  toggleFreeDraw: function (event) {
    if (this.drawingCanvas.isDrawingMode) {
      $(event.currentTarget).text("Draw");
      this.drawingCanvas.isDrawingMode = false;
    } else {
      $(event.currentTarget).text("Edit");
      this.drawingCanvas.isDrawingMode = true;
    }
  }
});

var UserView = Backbone.View.extend({
  className: 'author-box',

  events: {
    'click .f-button': 'follow',
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


var AppRouter = Backbone.Router.extend({
  routes: {
    "*actions": "defaultRoute"
  }
});

var app_router = new AppRouter();

app_router.on('route:defaultRoute', function () {
  this.mainModel = new StepModel();
  this.mainView = new TextEntryView({model: this.mainModel});
  $('.t-button').on('click', $.proxy(this.mainView.submitText, this.mainView));
});

Backbone.history.start();
