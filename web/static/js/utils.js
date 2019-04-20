$(document).ready(function () {
    var navbar = document.getElementById("top-navbar");
    var nav_items = navbar.getElementsByTagName('a');

    for (var i = 0; i < nav_items.length; ++i) {
        if (nav_items.item(i).href.toString() == document.location.toString()) {
            nav_items.item(i).className += " active";
            break;
        }
    }
});

function createForm(o, outter = 'tr') {
    let tr = $(o).closest(outter);
    let form = $('<form method="POST"></form>');
    form.append(tr.find('input[name="id"]'));
    let hidden_csrf = $('<input type="hidden" name="csrf_token"/>');
    hidden_csrf.val(csrf_token.value);
    form.append(hidden_csrf);
    return form;
}

$(document).ready(function () {
    $('.group-edit').click(function () {
        // Disable other rows
        $('.group-edit').prop("disabled", true);
        $('.group-delete').prop("disabled", true);

        // Make us an (enabled) save button
        $(this).prop("disabled", false);
        $(this).removeClass("file-edit");
        $(this).html("Save");

        // Enable the text fields on this row
        let tr = $(this).closest('tr');
        tr.find('input').prop("readonly", false);
        tr.find('input').prop("disabled", false);

        // Then when they click save
        $(this).click(function () {
            // Create a temp form with the inputs for the row they hit submit on
            let form = createForm(this);
            form.append(tr.find('input'));
            form.append($('<input type="hidden" name="action" value="update"/>'));
            form.appendTo('body').submit();
        });
    });

    $('.group-delete').click(function () {
        let form = createForm(this);
        form.append($('<input type="hidden" name="action" value="delete"/>'));
        form.appendTo('body').submit();
    });

    $('.photo-delete').click(function () {
        let form = createForm(this, 'span');
        form.append($('<input type="hidden" name="action" value="delete"/>'));
        form.appendTo('body').submit();
    });

    $('.comment-post').click(function () {
        let form = createForm(this, '#modalCommentForm');
        let outter = $(this).closest('#modalCommentForm');
        form.append(outter.find('textarea[name="content"]'));
        form.append($('<input type="hidden" name="action" value="comment"/>'));
        form.appendTo('body').submit();
    });

    $('.follow-user').click(function () {
        let form = createForm(this, '.card');
        form.append($('<input type="hidden" name="action" value="follow"/>'));
        form.appendTo('body').submit();
    });

    $('.accept-not').click(function () {
        let form = createForm(this, 'li');
        let outter = $(this).closest(".notification");
        form.append(outter.find('input[name="type"]'));
        form.append($('<input type="hidden" name="action" value="accept">'));
        form.appendTo('body').submit();
    });

    $('.reject-not').click(function () {
        let form = createForm(this, 'li');
        let outter = $(this).closest(".notification");
        form.append(outter.find('input[name="type"]'));
        form.append($('<input type="hidden" name="action" value="reject">'));
        form.appendTo('body').submit();
    });
});

