$(function(){
    // Implementing functionality for Login Function
    $('#login-button').click(function(){
        $('#login-form-hidden').show()
    })

    let votecount = '{{post.Votes}}'
    console.log(votecount)
    // $('.upvote').click(function(){
        
    // })

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

})