/**
 * Created by jbbrokaw on 12/12/2014.
 */
var textEntrySource   = $("#text-entry").html();
var textEntryTemplate = Handlebars.compile(textEntrySource);

var Subject = Backbone.Model.extend({
  url: '/subject',
  defaults: {
    'title': 'Enter the subject of a sentence',
    'instructions': 'Like "The happy brown bear"'
  }
});

var SubjectView = Backbone.View.extend({

  events: {
    'click button': 'submitSubject'
  },

  render: function () {
    this.setElement($('#content').empty().get(0));
    $(this.el).html(textEntryTemplate(this.model.toJSON()));
    return this;
  },

  submitSubject: function () {
    console.log("submitting whatever here");
    if ($('#prompt-entry').val() === "") {
      alert("You have to type something in the entry box");
      return;
    }
    var payload = {'prompt': $('#prompt-entry').val(),
               'csrf_token': $('#csrf').val()};
    $.post('/subject', payload).done(function (model, response, options) {
      console.log("Save succeeded.");
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
  this.subject = new Subject();
  this.subjectView = new SubjectView({model: this.subject});
  this.subjectView.render();
});

// Start Backbone history a necessary step for bookmarkable URL's
Backbone.history.start();