$(function() {
    $('#business_autocomplete').autocomplete({
        source: '/api/search',
        minLength: 2,
        delay: 250,
        messages: {
            noResults: '',
            results: function() {
                return '';
            }
        }
    });
});
