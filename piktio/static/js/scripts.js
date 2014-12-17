/**
 * Created by jbbrokaw on 12/12/2014.
 */
var textEntrySource   = $("#text-entry").html();
var textEntryTemplate = Handlebars.compile(textEntrySource);

var TextArea = Backbone.Model.extend({
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

  next_step: function (view) {
    return function (server_response) {
      if (typeof(server_response.error) !== 'undefined') {
        alert(server_response.error);
        return;
      }
      if (server_response.route.search('predicate') > -1) {
        view.model.clear().set(server_response);
        view.render();
        return;
      }
      console.log('route for new thing didn\'t include predicate');
      // Make a drawing ...
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

Backbone.history.start();
