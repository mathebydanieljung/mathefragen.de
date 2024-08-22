var Answer_v1 = {};

Answer_v1.init = function (answer_id) {
    this.answer_id = answer_id;
};

Answer_v1.vote = function (vote_type, reason) {
    var dfd = $.Deferred();
    $.ajax({
        url: '/vote/answer/' + this.answer_id + '/',
        type: 'post',
        data: {
            answer: this.answer_id,
            vote_type: vote_type,
            reason: reason,
            csrfmiddlewaretoken: csrf_token
        }
    }).done(function(res) {
        dfd.resolve(res);
    }).fail(function(){
        dfd.reject();
    });
    return dfd;
};

Answer_v1.mark_accepted = function (grasp_level) {
    $.ajax({
        url: accept_url,
        type: 'post',
        data: {
            answer_id: this.answer_id,
            grasp_level: grasp_level,
            csrfmiddlewaretoken: csrf_token
        }
    });
};

Answer_v1.update_text = function (text) {
    $.ajax({
        url: answer_update_url,
        type: 'post',
        data: {
            answer_id: this.answer_id,
            text: text,
            csrfmiddlewaretoken: csrf_token
        }
    });
};

Answer_v1.delete_answer = function () {
    $.ajax({
        url: answer_delete_url,
        type: 'post',
        data: {
            answer_id: this.answer_id,
            csrfmiddlewaretoken: csrf_token
        }
    });
};




