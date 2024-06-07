from apps.chat.models import Chat, Message
from django.db import models
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from apps.user_cabinet.models import Contacts
from apps.chat.models import ChatUserStatus

User = get_user_model()


@login_required(login_url='login')
def chats(request):
    user = request.user
    chat_rooms = Chat.objects.filter(
        Q(user_first=user) | Q(user_second=user)
    ).select_related('user_first', 'user_second').prefetch_related('user_statuses')

    favorite_chats = []
    deleted_chats = []
    chat_details = []

    for chat in chat_rooms:
        status = chat.user_statuses.get(user=user)
        messages = Message.objects.filter(chat=chat).order_by('-created_at')
        unread_count = messages.filter(is_read=False).exclude(sender=user).count()

        if status.is_deleted:
            deleted_chats.append({
                'chat': chat,
                'last_message': messages.first(),
                'unread_count': unread_count
            })
        elif status.is_favorite:
            favorite_chats.append({
                'chat': chat,
                'last_message': messages.first(),
                'unread_count': unread_count
            })
        else:
            chat_details.append({
                'chat': chat,
                'last_message': messages.first(),
                'unread_count': unread_count
            })

    contacts = Contacts.load()

    return render(request, 'chat_list.html', {
        'chat_details': chat_details,
        'contacts': contacts,
        'favorite_chats': favorite_chats,
        'deleted_chats': deleted_chats
    })


@login_required(login_url='/login/')
def chat_detail(request, pk):
    chat = get_object_or_404(Chat, id=pk)
    messages = Message.objects.filter(chat=chat).order_by('created_at')
    unread_messages = messages.filter(is_read=False).exclude(sender=request.user)
    unread_messages.update(is_read=True)
    return render(request, 'chat.html', {'chat': chat, 'messages': messages})


def create_chat(request, pk):
    user = get_object_or_404(User, id=pk)

    # Проверяем, существует ли уже чат между этими двумя пользователями
    existing_chat = Chat.objects.filter(
        (Q(user_first=request.user) & Q(user_second=user)) |
        (Q(user_first=user) & Q(user_second=request.user))
    ).first()

    if existing_chat:
        # Если чат существует, редиректим к нему
        return redirect(f'/chat/{existing_chat.id}')

    # Если чата нет, создаем новый
    chat = Chat.objects.create(user_first=request.user, user_second=user)

    ChatUserStatus.objects.create(chat=chat, user=request.user)
    ChatUserStatus.objects.create(chat=chat, user=user)

    return redirect(f'/chat/{chat.id}')


@login_required
def add_to_favorites(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    status, created = ChatUserStatus.objects.get_or_create(chat=chat, user=request.user)
    status.is_favorite = True
    status.save()
    return redirect('chat_list')

@login_required
def remove_from_favorites(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    status, created = ChatUserStatus.objects.get_or_create(chat=chat, user=request.user)
    status.is_favorite = False
    status.save()
    return redirect('chat_list')

@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    status, created = ChatUserStatus.objects.get_or_create(chat=chat, user=request.user)
    status.is_deleted = True
    status.save()
    return redirect('chat_list')

@login_required
def remove_from_deleted(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    status, created = ChatUserStatus.objects.get_or_create(chat=chat, user=request.user)
    status.is_deleted = False
    status.save()
    return redirect('chat_list')
