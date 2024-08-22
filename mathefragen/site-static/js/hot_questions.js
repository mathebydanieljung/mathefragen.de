function insert_hot_question_in_dom(questions){
    questions.forEach(function (question, index) {
        const p = document.createElement('p');
        p.className = 'promotion_p';

        const a = document.createElement('a');
        a.className = 'link_color light_bold';
        a.href = question.link;
        a.innerText = question.title;
        a.target = '_blank';

        p.append(a);

        if (question.link) {
            $('#hot_questions_parent_el').append(p);
            $('#hot_questions_aside').removeClass('d-none');
        }
    });

}

$(function (){
    hot_question_apis.forEach(function (api_url, index) {
        $.ajax({
            url: api_url
        }).done(function (data) {
            if (typeof data === 'object' && data !== null) {
                insert_hot_question_in_dom(data);
            }
        });
    });
});
