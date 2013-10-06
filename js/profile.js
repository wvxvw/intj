$(function () {
      var id = document.location.href.replace(/^[^?#]+\/profile\/([^\/]+).*$/g, "$1") || 'me',
      editor = new EpicEditor();
      $.ajax({ url: '/profile/' + id, type: 'POST' })
          .success(function (data) {
                       data.followerId = 'followers-view';
                       data.followedId = 'followed-view';
                       $('#info').html(_.template($('#profile-tpl').val())(data));
                       $.ajax({ url: '/feed/' + id, type: 'POST' })
                           .success(function (data) {
                                        data.title = 'Feed';
                                        data.id = 'feeds-view';
                                        _.each(data.feeds, function (feed) {
                                                   feed.text = editor.settings.parser(
                                                       feed.text.replace('\\n', '\n'));
                                               });
                                        $('#feed').html(_.template($('#feeds-tpl').val())(data));
                                    });
                   });
      $('#follow').on(
          'click',
          function () { $.ajax({ url: '/follow/' + id, type: 'POST' }); });
      $('#unfollow').on(
          'click',
          function () { $.ajax({ url: '/unfollow/' + id, type: 'POST' }); });
  });