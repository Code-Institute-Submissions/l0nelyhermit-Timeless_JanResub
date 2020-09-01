function upvote(a){
    let votes = parseInt($(a).parent().children('div').text())
    let post_id =$(a).data('postid')
    votes += 1;
    $(a).parent().children('div').text(votes);
    $.ajax({
        url:'/upvote',
        type:'POST',
        contentType: 'application/json;charset=UTF-8',
        dataType:"json",
        data: JSON.stringify({'PostID':post_id,
                              'Votes': votes})
    });
}

function downvote(a){
    let votes = parseInt($(a).parent().parent('div').text())
    votes -=1;
    if(votes <0){
        votes = 0;
        $(a).parent().parent('div').text(votes);
    }else{
        $(a).parent().parent('div').text(votes);
    }
    $.ajax({
        url:'/downvote',
        type:'POST',
        contentType: 'application/json;charset=UTF-8',
        dataType:"json",
        data:JSON.stringify({'Votes':votes,
                             'PostID':$(a).data('postid')})
    })
    return false;
}

function like(a){
    let likes = parseInt($(a).parent().children('div').text())
    let like_id =$(a).data('listingid')
    likes += 1;
    $(a).parent().children('div').text(likes);
    $.ajax({
        url:'/like',
        type:'POST',
        contentType: 'application/json;charset=UTF-8',
        dataType:"json",
        data: JSON.stringify({'ListingID':like_id,
                              'Likes': likes})
    });
}

function hideAllPages() {
    let pages = $(".page");
    for (let p of pages) {
        $(p).removeClass('show');
        $(p).addClass('hidden')
    }
}

$('#page2-btn').click(function(){
    let pageNumber = $(this).data('page');
    hideAllPages();
    $(`#page-${pageNumber}`).addClass('show');
    $(`#page-${pageNumber}`).removeClass('hidden');
})

$('#filter-text-recent').click(function(event){
    event.preventDefault();
    window.location='/home?sort_on=Date_Posted'
})

$('#filter-text-popular').click(function(event){
    event.preventDefault();
    window.location='/home?sort_on=Votes'
})


$(function(){
    // Implementing functionality for Login Function


    $('#summernote').summernote({
        placeholder: 'Start creating your note here!',
        tabsize: 2,
        height: 300,
        stripTags: ['style'],
        fontSizes: ['8', '10', '12', '14', '16', '18', '20', '22', '24' , '36', '48', '64'],
        toolbar: [
            // [groupName, [list of button]]
            ['style', ['style', 'bold', 'italic', 'underline', 'clear']],
            ['font', ['strikethrough', 'superscript', 'subscript']],
            ['fontname', ['fontname']],
            ['fontsize', ['fontsize']],
            ['color', ['color']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['height', ['height']],
            ['insert', ['table']],
            ['view', ['fullscreen']]
        ]
    });

    $('#sidebarCollapse').on('click',function(){
        $('#sidebar,#content').toggleClass('active')
    })

     

})