var header_search_bar;
var header_menu_btn;
var header_menu_box;

var editor_section_box;
var editor_button_section_focused;

var editor_link_target;
var editor_link_display;
var editor_link_radio;

var menu_display = false;

var keydown_shift = false;

window.onload = function() {
	header_search_bar = document.getElementById('header_search_bar');
	header_menu_btn = document.getElementById('header_menu_btn');
	header_menu_box = document.getElementById('header_menu_box');


	editor_section_box = document.getElementById('editor_section_box');

	
	editor_link_target = document.getElementById('editor_link_target');
	editor_link_display = document.getElementById('editor_link_display');
	editor_link_radio = document.getElementsByName('editor_link_radio');

	edit_area = document.getElementById('edit_area');
}

function toggle_menu() {
	if (menu_display) {
		document.getElementById('header_menu_btn').childNodes[0].src = '/static/symbol_menu.svg'
		header_menu_box.style.display = 'none';
	}
	else {
		document.getElementById('header_menu_btn').childNodes[0].src = '/static/symbol_close.svg'
		header_menu_box.style.display = 'block';
	}
	menu_display = !menu_display;
}

function editor_select_insert_pair(token_front, token_back, empty_replace, position, select_again) {
	var start = edit_area.selectionStart;
	var end = edit_area.selectionEnd;
	var selected = edit_area.value.substring(start, end);
	if (start == end) {
		selected = empty_replace;
	}

	front_length = token_front.length;
	back_length = token_back.length;

	switch (position) {
		case 0: {
			selected = token_front + selected;
			back_length = 0;
			break;
		}
		case 1: {
			selected = token_front + selected + token_back;
			break;
		}
		case 2: {
			selected = selected + token_back;
			front_length = 0;
			break;
		}
	}
	edit_area.focus();
	document.execCommand('insertText', false, selected);
	end = start + selected.length;

	switch (select_again) {
		case 0: {
			break;
		}
		case 1: {
			edit_area.select();
			edit_area.selectionStart = start + front_length;
			edit_area.selectionEnd = end - back_length;
			break;
		}
		case 2: {
			edit_area.select();
			edit_area.selectionStart = start;
			edit_area.selectionEnd = end;
			break;
		}
			
	}
	
}

function editor_select_insert_single(token_text, empty_replace, position, select_again) {
	editor_select_insert_pair(token_text, token_text, empty_replace, position, select_again);
}

function editor_get_select_block() {
	var selection_start = edit_area.selectionStart;
	var selection_end = edit_area.selectionEnd;
	var edit_end = edit_area.value.length;
	block_start = selection_start;
	if (edit_area.value.charAt(block_start) == '\n') block_start--;
	while (edit_area.value.charAt(block_start) != '\n' && block_start != 0) block_start--;
	if (block_start != 0) block_start++;
	block_end = selection_end;
	while (edit_area.value.charAt(block_end) != '\n' && block_end != edit_end) block_end++;
	block_text = edit_area.value.substring(block_start, block_end);

	return {
		ss: selection_start,
		se: selection_end,
		bs: block_start,
		be: block_end,
		bt: block_text
	};
}

function editor_set_select_block(select_data) {
	edit_area.focus();
	edit_area.select();
	edit_area.selectionStart = select_data.bs;
	edit_area.selectionEnd = select_data.be;
	document.execCommand('insertText', false, select_data.bt);
	edit_area.select();
	edit_area.selectionStart = select_data.ss;
	edit_area.selectionEnd = select_data.se;
}

function editor_insert_tab() {
	select_data = editor_get_select_block();

	if (select_data.ss != select_data.se) {
		block_text_lines = select_data.bt.split('\n');
		select_data.bt = block_text_lines.join('\n\t');
		select_data.bt = '\t' + select_data.bt;
		tab_count = block_text_lines.length;
		if (select_data.bs != select_data.ss) {
			if (edit_area.value.charAt(select_data.ss - 1) != '\t') {
				select_data.ss++;
			}
		}
		select_data.se += tab_count;
		editor_set_select_block(select_data);
	}
	else editor_select_insert_single('\t', '', 0, 0);
}

function editor_remove_tab() {
	select_data = editor_get_select_block();

	block_text_lines = select_data.bt.split('\n\t');
	select_data.bt = block_text_lines.join('\n');
	tab_count = block_text_lines.length;
	if (select_data.bs != select_data.ss)
		if (edit_area.value.charAt(select_data.ss) != '\t') {
			if (select_data.bt.charAt(0) == '\t')
				select_data.ss--;
		}
	else if (select_data.be == select_data.se);
		tab_count--;
	console.log(edit_area.value.charCodeAt(select_data.ss));
	if (select_data.bt.charAt(0) == '\t') {
		select_data.bt = select_data.bt.substring(1);
		tab_count++;
	}
	select_data.se -= tab_count;
	editor_set_select_block(select_data);
}

function editor_extend_link(btn) {
	editor_extend_box('editor_link', btn);
	editor_select_link();
}

function editor_select_link() {
	selection_start = edit_area.selectionStart;
	selection_end = edit_area.selectionEnd;

	editor_link_target.value = edit_area.value.substring(selection_start, selection_end);
}

function editor_insert_link() {
	link_target = editor_link_target.value;
	link_display = editor_link_display.value;
	link_radio = 0;
	for (var i = 0; i < editor_link_radio.length; i++) {
		if (editor_link_radio[i].checked) {
			link_radio = i;
			break;
		}
	}
	link_text = ''
	if (link_display == '') {
		if (link_radio == 0) {
			link_text = '[[' + link_target + ']]';
		}
		else  {
			link_text = '<' + link_target  + '>';
		}
	}
	else {
		if (link_radio == 0) {
			link_text = '[[' + link_target + '|' + link_display + ']]';
		}
		else {
			link_text = '[' + link_display  + '](' + link_target + ' "' + link_display + '")';
		}
	}
	edit_area.focus();
	document.execCommand('insertText', false, link_text);
	editor_close_section()
}

function editor_close_section() {
	editor_extend_box('editor_link', editor_button_section_focused);
}

function editor_extend_box(id, btn) {
	var block_section;
	for (var i = 0; i < editor_section_box.childNodes.length; i++) {
		var section = editor_section_box.childNodes[i];
		if (section.id == id) {
			block_section = section;
		}
		else if (section.id != undefined) {
			section.style.display = 'none';
		}
	}
	if (editor_button_section_focused != undefined) {
		editor_button_section_focused.removeAttribute('style');
	}
	if (editor_button_section_focused != btn) {
		editor_button_section_focused = btn;
		editor_button_section_focused.style.backgroundColor = '#dfdfdf';
		block_section.style.display = 'block';
	}
	else {
		block_section.style.display = 'none';
		btn.removeAttribute('style');
		editor_button_section_focused = undefined;
	}
	btn.blur();
	edit_area.focus()
}

function editor_keydown(event) {
	switch (event.keyCode) {
		case 9: {
			event.preventDefault();
			if (keydown_shift) {
				editor_remove_tab();
			}
			else {
				editor_insert_tab();
			}
			break;
		}
		case 16: {
			keydown_shift = true;
			break;
		}
	}
}

function editor_keyup(event) {
	switch (event.keyCode) {
		case 16: {
			keydown_shift = false;
			break;
		}
	}
}