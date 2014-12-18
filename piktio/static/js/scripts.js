/**
 * Created by jbbrokaw on 12/12/2014.
 */
var textEntrySource   = $("#text-entry-template").html();
var textEntryTemplate = Handlebars.compile(textEntrySource);

var drawingSource = $("#drawing-template").html();
var drawingTemplate = Handlebars.compile(drawingSource);

var StepModel = Backbone.Model.extend({
  defaults: {
    'title': 'Enter the subject of a sentence',
    'instructions': 'Like "The happy brown bear"',
    'route': '/subject'
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
    if (!this.model.has('csrf_token')) {
      this.model.set('csrf_token', $('#csrf').val());
    }
    return this;
  },

  next_step: function (view) {
    return function (server_response) {
      if (typeof(server_response.error) !== 'undefined') {
        alert(server_response.error);
        return;
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
      console.log("Rendered view");
      console.log(view);
      app_router.mainView = view;
    };
  },

  submitText: function () {
    if ($('#prompt-entry').val() === "") {
      alert("You have to type something in the entry box");
      return;
    }
    this.model.set('prompt', $('#prompt-entry').val());
    var payload = this.model.toJSON();
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
    'click #clear': 'clear'
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

    return this;
  },

  next_step: function (view) {
    return function (server_response) {
      if (typeof(server_response.error) !== 'undefined') {
        alert(server_response.error);
        return;
      }
      //Make a description-entry view
      console.log('Make a description-entry view');
      console.log(server_response)
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
    this.model.set('drawing', this.drawingCanvas.toDataURL('png'));
    var payload = this.model.toJSON();
    $.post(this.model.get('route'), payload)
      .done(this.next_step(this))
      .fail(function (response) {
        console.log(response);
    });
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
  this.mainView.render();
});

Backbone.history.start();
