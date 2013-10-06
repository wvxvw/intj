$(function () {
      var id = document.location.href.replace(/^[^?#]+\/article\/([^\/]+).*$/g, "$1") || '';
      $.ajax({ url: '/article/' + id, type: 'POST' })
          .success(function (data) {
                       $('#article').html(
                           new EpicEditor().settings.parser(data.replace('\\n', '\n')));
                   });
  });