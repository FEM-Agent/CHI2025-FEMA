$(document).ready(function () {
    let currentProjectName = '';
    let previousDepth = 0;

    function bindCommentToggle() {
        $('.comments-toggle').off('click').on('click', function () {
            $(this).siblings('.comments-list').toggle();
        });
    }

    function updateSliderBackground(currentValue, initialValue) {
        let currentPercentage = (currentValue / 5) * 100;
        let initialPercentage = (initialValue / 5) * 100;
        $('#depthRange').css('background', 'linear-gradient(to right, #1e3a8a 0%, #1e3a8a ' + currentPercentage + '%, #4c7efb ' + currentPercentage + '%, #4c7efb ' + initialPercentage + '%, #ccc ' + initialPercentage + '%, #ccc 100%)');
    }

    function updateDepthValue(depth, initialValue) {
        $('#depthRange').val(depth);
        $('#depthValue').text(depth);
        updateSliderBackground(depth, initialValue);
        if (depth > initialValue) {
            $('#simulation-modal').show();
        } else {
            previousDepth = depth;
        }
    }

    $('#depthIncrease').on('click', function () {
        var depth = parseInt($('#depthRange').val());
        var initialValue = parseInt($('#depthRange').data('initial-value'));
        if (depth < 5) {
            depth++;
            updateDepthValue(depth, initialValue);
            filterTweets();
        }
    });

    $('#depthDecrease').on('click', function () {
        var depth = parseInt($('#depthRange').val());
        var initialValue = parseInt($('#depthRange').data('initial-value'));
        if (depth > 0) {
            depth--;
            updateDepthValue(depth, initialValue);
            filterTweets();
        }
    });

    $('#search-input').on('keypress', function (e) {
        if (e.which === 13) {
            var searchQuery = $(this).val().toLowerCase();
            filterTweets(searchQuery);
        }
    });

    function filterTweets(searchQuery = '') {
        var depth = $('#depthRange').val();

        $('.tweet-container').each(function () {
            var tweetDepth = $(this).data('depth');
            var tweetContent = $(this).find('.tweet-content').text().toLowerCase();
            var tweetMatches = tweetDepth <= depth && tweetContent.includes(searchQuery);

            // 过滤评论
            var hasVisibleComments = filterComments($(this), depth, searchQuery);

            // 如果 Tweet 自己匹配或者它有匹配的评论，则显示 Tweet，否则隐藏
            if (tweetMatches || hasVisibleComments) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });

        updateCommentCounts(depth, searchQuery);
    }

    function filterComments(tweetElement, depth, searchQuery) {
        var hasVisibleComments = false;
        tweetElement.find('.comment-container').each(function () {
            var commentDepth = $(this).data('depth');
            var commentContent = $(this).find('.comment-content').text().toLowerCase();
            var commentMatches = commentDepth <= depth && commentContent.includes(searchQuery);

            if (commentMatches) {
                $(this).show();
                hasVisibleComments = true;
            } else {
                $(this).hide();
            }

            // 递归过滤子评论
            if (filterComments($(this), depth, searchQuery)) {
                $(this).show();
                hasVisibleComments = true;
            }
        });
        return hasVisibleComments;
    }

    function updateCommentCounts(depth, searchQuery) {
        $('.tweet-container').each(function () {
            var commentCount = 0;
            $(this).find('.comment-container').each(function () {
                var commentDepth = $(this).data('depth');
                var commentContent = $(this).find('.comment-content').text().toLowerCase();
                if (commentDepth <= depth && commentContent.includes(searchQuery)) {
                    commentCount++;
                }
            });
            $(this).find('.comments-count').text(commentCount);
        });
    }

    $('#add-event').on('click', function () {
        var newEvent = $('#new-event-input').val().trim();
        if (newEvent) {
            var newEventIndex = $('#events-list .event-item').length + 1;
            var eventItem = $('' +
                '<li class="event-item" data-project-name="' + newEventIndex + '">' +
                '<span class="event-number">' + newEventIndex + '</span>' +
                '<div class="event-details">' +
                '<span class="event-description">' + newEvent + '</span><button class="delete-event">Delete</button></div></li>');
            $('#events-list').append(eventItem);
            $('#new-event-input').val('');
            saveEvents();
        }
    });

    $(document).on('click', '.delete-event', function () {
        $(this).closest('.event-item').remove();
        updateEventNumbers();
        saveEvents();
    });

    function updateEventNumbers() {
        $('#events-list .event-item').each(function (index) {
            $(this).find('.event-number').text(index + 1);
        });
    }

    function saveEvents() {
        var events = [];
        $('#events-list .event-description').each(function () {
            events.push($(this).text());
        });

        $.ajax({
            url: '/api/events',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({events: events}),
            success: function (response) {
                console.log('Events saved successfully!');
            },
            error: function (error) {
                console.log('Error saving events: ' + error.responseText);
            }
        });
    }

    $(document).on('click', '.event-item', function () {
        $('.event-item').removeClass('selected');
        $(this).addClass('selected');
        var eventContent = $(this).find('.event-description').text();
        currentProjectName = $(this).data('project-name');
        loadEventData(eventContent, currentProjectName);
    });

    function loadEventData(eventContent, projectName) {
        $.ajax({
            url: '/api/event_data',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({event: eventContent}),
            success: function (response) {
                updateUI(response.tweets, response.agents, response.max_depth);
                bindCommentToggle();
            },
            error: function (error) {
                console.log('Error loading event data: ' + error.responseText);
            }
        });
    }

    function renderComments(comments) {
        let commentHtml = '';
        comments.forEach(function (comment) {
            commentHtml += '<div class="comment-container" data-depth="' + comment.depth + '">';
            commentHtml += '<div class="comment">';
            commentHtml += '<div class="comment-author">' + comment.author + '</div>';
            commentHtml += '<div class="comment-time">' + comment.tweet_time + '</div>';
            commentHtml += '<div class="comment-content">' + comment.content + '</div>';
            commentHtml += '</div>';

            // 递归渲染子评论
            if (comment.comments && comment.comments.length > 0) {
                commentHtml += '<div class="nested-comments">';
                commentHtml += renderComments(comment.comments);
                commentHtml += '</div>';
            }

            commentHtml += '</div>'; // 关闭 comment-container
        });
        return commentHtml;
    }

    function updateUI(tweets, agents, maxDepth) {
        $('#depthRange').attr('max', 5);
        $('#depthRange').data('initial-value', maxDepth);
        updateDepthValue(maxDepth, maxDepth);

        var tweetsContainer = $('#tweets-container');
        tweetsContainer.empty();
        tweets.forEach(function (tweet) {
            var tweetItem = `
            <div class="tweet-container" data-depth="${tweet.depth}" data-hash-id="${tweet.hash_id}">
                <div class="title">
                    ${tweet.author}
                    <button class="delete-post">Delete</button> <!-- Delete button inside the title div -->
                </div>
                <div class="tweet-time">${tweet.tweet_time}</div>
                <div class="tweet-content">${tweet.content}</div>
                <div class="tweet-likes">
                    <img src="/static/like.png" alt="Likes" class="icon">
                    <span class="likes-list">${tweet.likes.join(', ')}</span>
                </div>
                <div class="tweet-comments">
                    <span class="comments-toggle">
                        <img src="/static/comments.png" alt="Comments" class="icon">
                        <span class="comments-count">${tweet.total_comments}</span>
                    </span>
                    <div class="comments-list" style="display: none;">
                        ${renderComments(tweet.comments)}
                    </div>
                </div>
            </div>`;
            tweetsContainer.append(tweetItem);
        });

        var agentsContainer = $('.npc-list');
        agentsContainer.empty();
        agents.forEach(function (agent) {
            var statusDotColor = agent.online ? 'green' : 'red';
            var switchState = agent.online ? 'checked' : '';
            var agentItem = `
            <li class="npc-item" data-id="${agent.id}" data-name="${agent.name}" data-occupation="${agent.occupation}"
                data-experience="${agent.experience}" data-character="${agent.character}"
                data-interest="${agent.interest}" data-online="${agent.online}">
                <strong class="npc-name">
                    <span class="status-dot" style="background-color: ${statusDotColor};"></span>
                    ${agent.name}
                    <button class="edit-agent">Edit</button>
                    <label class="switch">
                        <input type="checkbox" class="toggle-online" ${switchState}>
                        <span class="slider round"></span>
                    </label>
                </strong>
                <br>
                <div class="npc-section">
                    <img src="/static/character.png" alt="Character Icon">
                    <span style="color: #4C7DFB; opacity: 50%">${agent.character}</span>
                    <button class="delete-agent">Delete</button>
                </div>
            </li>`;
            agentsContainer.append(agentItem);
        });
    }


    $(document).on('click', '.delete-post', function () {
        var tweetContainer = $(this).closest('.tweet-container');
        var tweetHashId = tweetContainer.data('hash-id');

        $.ajax({
            url: '/api/delete_post?project_name=' + currentProjectName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({hash_id: tweetHashId}),
            success: function (response) {
                console.log('Post deleted successfully!');
                tweetContainer.remove(); // Remove the tweet from the UI
            },
            error: function (error) {
                console.log('Error deleting post: ' + error.responseText);
            }
        });
    });


    $(document).on('click', '.edit-agent', function () {
        var agentItem = $(this).closest('.npc-item');
        var id = agentItem.data('id');
        var name = agentItem.data('name');
        var occupation = agentItem.data('occupation');
        var experience = agentItem.data('experience');
        var character = agentItem.data('character');
        var interest = agentItem.data('interest');

        $('#npc-id').val(id);
        $('#npc-name').val(name);
        $('#npc-occupation').val(occupation);
        $('#npc-experience').val(experience);
        $('#npc-character').val(character);
        $('#npc-interest').val(interest);

        $('#npc-detail-modal').show();
    });

    $(document).on('click', '.delete-agent', function () {
        var agentItem = $(this).closest('.npc-item');
        var agentId = agentItem.data('name');
        deleteAgent(agentId);
        agentItem.remove();
    });

    $(document).on('change', '.toggle-online', function () {
        var agentItem = $(this).closest('.npc-item');
        var agentName = agentItem.data('name');
        var onlineStatus = $(this).is(':checked');

        toggleAgentOnline(agentName, onlineStatus);
    });

    function toggleAgentOnline(agentName, onlineStatus) {
        $.ajax({
            url: '/api/toggle_online_agent?project_name=' + currentProjectName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({name: agentName, online: onlineStatus}),
            success: function (response) {
                console.log('Agent online status updated successfully!');
                loadEventData(currentProjectName, currentProjectName);
            },
            error: function (error) {
                console.log('Error updating agent online status: ' + error.responseText);
            }
        });
    }

    $('#add-agent').on('click', function () {
        $('#add-agent-modal').show();
    });

    $('#cancel-add-agent').on('click', function () {
        $('#add-agent-modal').hide();
    });

    $('#confirm-add-agent').on('click', function () {
        var name = $('#new-agent-name').val();
        var occupation = $('#new-agent-occupation').val();
        var experience = $('#new-agent-experience').val();
        var character = $('#new-agent-character').val();
        var interest = $('#new-agent-interest').val();

        var newAgent = {
            name: name,
            occupation: occupation,
            experience: experience,
            character: character,
            interest: interest
        };

        addAgent(newAgent);
        $('#add-agent-modal').hide();
    });

    function deleteAgent(agentName) {
        $.ajax({
            url: '/api/delete_agent?project_name=' + currentProjectName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({name: agentName}),
            success: function (response) {
                console.log('Agent deleted successfully!');
                loadEventData(currentProjectName, currentProjectName); // 重新加载事件数据以刷新UI
            },
            error: function (error) {
                console.log('Error deleting agent: ' + error.responseText);
            }
        });
    }

    function addAgent(newAgent) {
        $.ajax({
            url: '/api/add_agent?project_name=' + currentProjectName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(newAgent),
            success: function (response) {
                console.log('Agent added successfully!');
                loadEventData(currentProjectName, currentProjectName);
            },
            error: function (error) {
                console.log('Error adding agent: ' + error.responseText);
            }
        });
    }

    $('#close-modal, #cancel-edit').on('click', function () {
        $('#npc-detail-modal').hide();
    });

    $('#confirm-edit').on('click', function () {
        var id = $('#npc-id').val();
        var name = $('#npc-name').val();
        var occupation = $('#npc-occupation').val();
        var experience = $('#npc-experience').val();
        var character = $('#npc-character').val();
        var interest = $('#npc-interest').val();

        $.ajax({
            url: '/api/update_agent?project_name=' + currentProjectName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                id: id,
                name: name,
                occupation: occupation,
                experience: experience,
                character: character,
                interest: interest
            }),
            success: function (response) {
                console.log('Agent updated successfully!');
                $('#npc-detail-modal').hide();
                loadEventData(currentProjectName, currentProjectName);
            },
            error: function (error) {
                console.log('Error updating agent: ' + error.responseText);
            }
        });
    });

    $('#cancel-simulation').on('click', function () {
        var initialValue = parseInt($('#depthRange').data('initial-value'));
        updateDepthValue(previousDepth, initialValue);
        $('#simulation-modal').hide();
    });

    $('#confirm-simulation').on('click', function () {
        var currentDepth = $('#depthRange').val();

        // 显示处理中的模态框
        $('#processing-modal').show();

        $.ajax({
            url: '/api/simulate?project_name=' + currentProjectName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({depth: currentDepth}),
            success: function (response) {
                console.log('Simulation confirmed at depth:', currentDepth);

                // 隐藏处理中的模态框
                $('#processing-modal').hide();

                // 重新加载事件数据
                loadEventData(currentProjectName, currentProjectName);
            },
            error: function (error) {
                console.log('Error confirming simulation: ' + error.responseText);

                // 隐藏处理中的模态框，即使出错也要隐藏
                $('#processing-modal').hide();
            }
        });
    });

    $(window).on('click', function (event) {
        if ($(event.target).is('#npc-detail-modal')) {
            $('#npc-detail-modal').hide();
        }
        if ($(event.target).is('#simulation-modal')) {
            $('#simulation-modal').hide();
        }
        if ($(event.target).is('#add-agent-modal')) {
            $('#add-agent-modal').hide();
        }
    });

    $('#post-by-yourself').on('click', function () {
        $('#post-modal').show();
    });

    $('#cancel-post, #close-post-modal').on('click', function () {
        $('#post-modal').hide();
    });

    $('#confirm-post').on('click', function () {
        var author = $('#post-author').val();
        var content = $('#post-content').val();
        if (author && content) {
            $('#loading-modal').show();  // Show loading modal

            $.ajax({
                url: '/api/add_post_to_queue?project_name=' + currentProjectName,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({author: author, content: content}),
                success: function (response) {
                    console.log('Post added successfully!');
                    $('#loading-modal').hide();  // Hide loading modal
                    $('#post-modal').hide();  // Automatically close the post modal
                    loadEventData(currentProjectName, currentProjectName);  // Refresh the event data
                },
                error: function (error) {
                    console.log('Error adding post: ' + error.responseText);
                    $('#loading-modal').hide();  // Hide loading modal even if there's an error
                }
            });
        } else {
            alert("Please fill in both the Author and Content fields.");
        }
    });

    $(window).on('click', function (event) {
        if ($(event.target).is('#post-modal')) {
            $('#post-modal').hide();
        }
    });

    function selectFirstEvent() {
        var firstEvent = $('#events-list .event-item').first();
        if (firstEvent.length) {
            firstEvent.addClass('selected');
            var eventContent = firstEvent.find('.event-description').text();
            currentProjectName = firstEvent.data('project-name');
            loadEventData(eventContent, currentProjectName);
        }
    }

    selectFirstEvent();
});
