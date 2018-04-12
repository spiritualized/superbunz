function addToSection(story, section)
{
	var button_class = "btn-success";
	var button_text = "Save"
	if(story.saved == 1)
	{
		button_class = "btn-danger";
		button_text = "Unsave";
	}

	$('#table-'+section+' > tbody:last-child')
		.append($('<tr>').attr('class','table-'+section+'-row')
			.append($('<td>').attr('style', 'text-align:center;').attr('class', 'table-col-left' )
				.append($('<a>').attr('href', 'https://facebook.com/'+story.username).attr('style', 'color:inherit;').attr('target', 'none')
					.append($('<img>')
						.attr('src', story.user_picture)
						.text('User image')
						.attr('class', 'rounded-circle img-fluid')
					)
					.append($('<br />')
					)
					.append($('<span>').text(story.name)
					)
				)
			)
			
			.append($('<td>').html(story.description).attr('style', 'word-wrap:normal;')
			)

			.append($('<td>')
				.append($("<table>").attr('class','details-table')
					.append($("<tr>").attr('class', 'user-right')
						.append($("<td>").attr('style', 'text-align:center;')
							.append($('<a>').attr('href', 'https://facebook.com/'+story.username).attr('style', 'color:inherit;').attr('target', 'none')
								.append($('<img>')
									.attr('src', story.user_picture)
									.text('User image')
									.attr('class', 'rounded-circle img-fluid')
								)
								.append($('<br />')
								)
								.append($('<span>').text(story.name)
								)
							)
						)
					)
					.append($("<tr>")
						.append($("<td>").html(story.age)
						)
					)
					.append($("<tr>")
						.append($("<td>").html(story.cost).attr('class', 'cost-td')
						)
					)
					.append($("<tr>")
						.append($("<td>").append($('<a>').attr('href', 'https://www.facebook.com/groups/bunzhomezone/permalink/'+story.story_id).attr('target', 'none')
							.append($("<button>").attr('class', 'btn btn-primary').text("View").attr('style', 'font-size:12px;'))
							)
						)
					)
					.append($("<tr>")
						.append($("<td>")
							.append($("<button>").attr('class', button_class+' btn button-save').text(button_text).attr('style', 'font-size:12px;').attr('data-story-id', story.story_id).attr('data-saved', story.saved)
							)
						)
					)
				)
			)
		);
}

function updatePage(data)
{
	$.get("/api", {'op': 'get_data'}, function(data){
		data = JSON.parse(data);

		//date =  new Date()
		$("#last-updated")[0].innerHTML = strftime('%B %d, %Y %H:%M:%S'); //.toLocaleString('en-CA');
		$("#users-online")[0].innerHTML = data.users_online;
		$("#max-cost")[0].value = data.max_cost;

		if(data.hide_sold)
			$("#hide-sold")[0].checked = "checked";
		
		// reload if the server software has been updated
		if($("#version")[0].innerHTML != "" && $("#version")[0].innerHTML != data.version)
		{
			location.reload();
		}
		$("#version")[0].innerHTML = data.version;

		$(".table-offers-row").remove();
		$(".table-other-row").remove();
		$(".table-saved-row").remove();

		for(i=0; i < data.offers.length; i++)
		{
			addToSection(data.offers[i], 'offers');
		}

		for(i=0; i < data.other.length; i++)
		{
			addToSection(data.other[i], 'other');
		}

		for(i=0; i < data.saved.length; i++)
		{
			addToSection(data.saved[i], 'saved');
		}
	});
}

$("#hide-sold").change(function(){
	$.get("/api", {'op': 'hide_sold', 'hide_sold': $(this)[0].checked}, function(data){
		updatePage();
	});
});

$("#max-cost").keyup($.debounce(500, function(){
	var max_cost = $(this)[0].value;

	var invalidChars = /[^0-9]/gi
	if(invalidChars.test(max_cost))
	{
		max_cost = max_cost.replace(invalidChars,"");
		$(this)[0].value = max_cost;
	}

	$.get("/api", {'op': 'max_cost', 'max_cost': max_cost}, function(data){
		updatePage();
	});
}));

// these buttons are dynamically added, thus a delegated event handler is necessary
$(document).on("click", ".button-save", function(){
	button = $(this);

	$.get("/api", {'op': 'save', 'story_id': button.attr('data-story-id'), 'existing':button.attr('data-saved')}, function(data){

		if(button.attr('data-saved') == 1)
		{
			button.removeClass('btn-danger');
			button.addClass('btn-success');
			button.text('Save');
			button.attr('data-saved', 0);

		}

		else
		{
			button.removeClass('btn-success');
			button.addClass('btn-danger');
			button.text('Unsave');
			button.attr('data-saved', 1);
		}

		updatePage();
	});
});


$( document ).ready(function() {
	updatePage();
	setInterval(updatePage, 60000);
});

