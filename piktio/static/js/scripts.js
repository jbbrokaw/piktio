/**
 * Created by jbbrokaw on 12/12/2014.
 */
var textEntrySource   = $("#text-entry").html();
var textEntryTemplate = Handlebars.compile(textEntrySource);

var TextArea = Backbone.Model.extend({
  url: '/subject',
  defaults: {
    'title': 'Enter the subject of a sentence',
    'instructions': 'Like "The happy brown bear"',
    'route': '/subject'
  }
});

var TextEntryView = Backbone.View.extend({

  events: {
    'click button': 'submitText'
  },

  render: function () {
    this.setElement($('#content').empty().get(0));
    $(this.el).html(textEntryTemplate(this.model.toJSON()));
    this.model.set('csrf_token', $('#csrf').val());
    return this;
  },

  submitText: function () {
    if ($('#prompt-entry').val() === "") {
      alert("You have to type something in the entry box");
      return;
    }
    this.model.set('prompt', $('#prompt-entry').val());
    var payload = this.model.toJSON();
    $.post(this.model.get('route'), payload)
      .done(function (model, response, options) {
        console.log("Save succeeded.");
        console.log(response);
        //response = JSON.parse(response);
        //$('#content').empty();
        //$('#content').html(response.html);
        //$('.drawing-prompt').text(response.prompt);
      })
      .fail(function (model, response, options) {
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
  this.subject = new TextArea();
  this.subjectView = new TextEntryView({model: this.subject});
  this.subjectView.render();
});

// Start Backbone history a necessary step for bookmarkable URL's
Backbone.history.start();