var Question_v1 = {};

Question_v1.init = function (question_id) {
    this.question_id =  question_id;
};

Question_v1.vote = function (vote_type, reason) {
    var dfd = $.Deferred();
    $.ajax({
        url: '/vote/question/' + this.question_id + '/',
        type: 'post',
        data: {
            question: this.question_id,
            reason: reason,
            vote_type: vote_type,
            csrfmiddlewaretoken: csrf_token
        }
    }).done(function(res) {
        dfd.resolve(res);
    }).fail(function(){
        dfd.reject();
    });
    return dfd;
};


Question_v1.save_comment = function (comment_text, question_id) {
    $.ajax({
        url: '/question/comment/save/',
        type: 'post',
        data: {
            question: question_id,
            comment_text: comment_text,
            csrfmiddlewaretoken: csrf_token
        }
    });
};

Question_v1.delete_comment = function (comment_id) {
    $.ajax({
        url: '/question/comment/delete/',
        type: 'post',
        data: {
            comment_id: comment_id,
            csrfmiddlewaretoken: csrf_token
        }
    });
};
