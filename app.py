import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

# --- Configurações Iniciais e Simulação de Banco de Dados ---
if 'initialized' not in st.session_state:
    st.session_state.users = [
        {"username": "admin", "password": "admin_password", "role": "admin"},
        {"username": "user1", "password": "user1_password", "role": "user"},
        {"username": "user2", "password": "user2_password", "role": "user"}
    ]
    st.session_state.rooms = [
        {"id": 1, "name": "Sala Alpha", "capacity": 10, "amenities": "Projetor, Quadro Branco"},
        {"id": 2, "name": "Sala Beta (VIP)", "capacity": 4, "amenities": "TV, Videoconferência"},
        {"id": 3, "name": "Auditório Gama", "capacity": 50, "amenities": "Projetor, Som, Palco"}
    ]
    st.session_state.requestable_items = [
        {"id": 1, "name": "Café (garrafa)", "description": "Garrafa térmica de café (aprox. 10 copos)"},
        {"id": 2, "name": "Água (garrafas individuais)", "description": "Garrafas de água mineral sem gás"},
        {"id": 3, "name": "Projetor Adicional", "description": "Caso a sala não possua ou necessite de um extra"},
        {"id": 4, "name": "Kit Lanche Simples", "description": "Pequeno lanche por pessoa"}
    ]
    st.session_state.meetings = [
        # Exemplo de reunião para teste
        {
            "id": 1, "title": "Reunião Kick-off Projeto X", "room_id": 1, "date": datetime.now().date(),
            "start_time": time(10, 0), "end_time": time(11, 0), "organizer": "user1",
            "priority": "Alta", "attendees": "user1, admin",
            "requested_items": [{"item_id": 1, "quantity": 1}, {"item_id": 2, "quantity": 5}],
            "status": "Confirmada"
        }
    ]
    st.session_state.next_meeting_id = 2
    st.session_state.next_room_id = 4
    st.session_state.next_item_id = 5
    st.session_state.logged_in_user = None
    st.session_state.initialized = True

# --- Funções Auxiliares ---
def get_room_name(room_id):
    for room in st.session_state.rooms:
        if room["id"] == room_id:
            return room["name"]
    return "Desconhecida"

def get_item_name(item_id):
    for item in st.session_state.requestable_items:
        if item["id"] == item_id:
            return item["name"]
    return "Desconhecido"

def check_room_availability(room_id, date, start_time, end_time, S_time, E_time):
    for meeting in st.session_state.meetings:
        if meeting["room_id"] == room_id and meeting["date"] == date:
            # Convert meeting times to comparable format (e.g., total minutes from midnight)
            meeting_start_minutes = meeting["start_time"].hour * 60 + meeting["start_time"].minute
            meeting_end_minutes = meeting["end_time"].hour * 60 + meeting["end_time"].minute
            requested_start_minutes = start_time.hour * 60 + start_time.minute
            requested_end_minutes = end_time.hour * 60 + end_time.minute
            if not (S_time == meeting["start_time"] and E_time == meeting["end_time"]): # Avoid conflict with itself when editing
                if max(meeting_start_minutes, requested_start_minutes) < min(meeting_end_minutes, requested_end_minutes):
                    return False  # Conflict
    return True # Available

# --- Interface de Login ---
def login_page():
    st.header("Login - Sistema de Agendamento Corporativo")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        for user in st.session_state.users:
            if user["username"] == username and user["password"] == password:
                st.session_state.logged_in_user = user
                st.rerun() # st.experimental_rerun in older versions
        st.error("Usuário ou senha inválidos.")

# --- Interface de Administrador ---
def admin_dashboard():
    st.sidebar.subheader(f"Bem-vindo, {st.session_state.logged_in_user['username']} (Admin)")
    admin_options = ["Visualizar Todas as Reuniões", "Gerenciar Salas", "Gerenciar Itens Solicitáveis", "Gerenciar Usuários"]
    choice = st.sidebar.radio("Menu Administrador", admin_options)

    if choice == "Visualizar Todas as Reuniões":
        admin_view_all_meetings()
    elif choice == "Gerenciar Salas":
        admin_manage_rooms()
    elif choice == "Gerenciar Itens Solicitáveis":
        admin_manage_items()
    elif choice == "Gerenciar Usuários":
        admin_manage_users()

def admin_view_all_meetings():
    st.subheader("Todas as Reuniões Agendadas")
    if not st.session_state.meetings:
        st.info("Nenhuma reunião agendada no momento.")
        return

    meetings_data = []
    for m in st.session_state.meetings:
        items_str = ", ".join([f"{req['quantity']}x {get_item_name(req['item_id'])}" for req in m["requested_items"]])
        meetings_data.append({
            "ID": m["id"],
            "Título": m["title"],
            "Sala": get_room_name(m["room_id"]),
            "Data": m["date"].strftime("%d/%m/%Y"),
            "Início": m["start_time"].strftime("%H:%M"),
            "Fim": m["end_time"].strftime("%H:%M"),
            "Organizador": m["organizer"],
            "Prioridade": m["priority"],
            "Itens": items_str if items_str else "Nenhum",
            "Status": m.get("status", "Confirmada") # Adicionado para compatibilidade
        })
    df_meetings = pd.DataFrame(meetings_data)
    st.dataframe(df_meetings, use_container_width=True)

def admin_manage_rooms():
    st.subheader("Gerenciar Salas")

    st.write("**Salas Existentes:**")
    if st.session_state.rooms:
        rooms_df = pd.DataFrame(st.session_state.rooms)
        st.table(rooms_df[["id", "name", "capacity", "amenities"]])
    else:
        st.info("Nenhuma sala cadastrada.")

    st.write("**Adicionar Nova Sala:**")
    with st.form("new_room_form", clear_on_submit=True):
        room_name = st.text_input("Nome da Sala")
        room_capacity = st.number_input("Capacidade", min_value=1, step=1)
        room_amenities = st.text_input("Comodidades (ex: Projetor, Wi-Fi)")
        submitted = st.form_submit_button("Adicionar Sala")
        if submitted and room_name:
            new_room = {
                "id": st.session_state.next_room_id,
                "name": room_name,
                "capacity": room_capacity,
                "amenities": room_amenities
            }
            st.session_state.rooms.append(new_room)
            st.session_state.next_room_id += 1
            st.success(f"Sala '{room_name}' adicionada com sucesso!")
            st.rerun()

def admin_manage_items():
    st.subheader("Gerenciar Itens Solicitáveis")

    st.write("**Itens Existentes:**")
    if st.session_state.requestable_items:
        items_df = pd.DataFrame(st.session_state.requestable_items)
        st.table(items_df[["id", "name", "description"]])
    else:
        st.info("Nenhum item cadastrado.")

    st.write("**Adicionar Novo Item:**")
    with st.form("new_item_form", clear_on_submit=True):
        item_name = st.text_input("Nome do Item")
        item_description = st.text_area("Descrição do Item")
        submitted = st.form_submit_button("Adicionar Item")
        if submitted and item_name:
            new_item = {
                "id": st.session_state.next_item_id,
                "name": item_name,
                "description": item_description
            }
            st.session_state.requestable_items.append(new_item)
            st.session_state.next_item_id += 1
            st.success(f"Item '{item_name}' adicionado com sucesso!")
            st.rerun()

def admin_manage_users():
    st.subheader("Gerenciar Usuários")

    st.write("**Usuários Existentes:**")
    users_display = [{"username": u["username"], "role": u["role"]} for u in st.session_state.users]
    users_df = pd.DataFrame(users_display)
    st.table(users_df)

    st.write("**Adicionar Novo Usuário:** (MVP Simplificado - sem edição/remoção)")
    with st.form("new_user_form", clear_on_submit=True):
        new_username = st.text_input("Nome do Usuário")
        new_password = st.text_input("Senha", type="password")
        new_role = st.selectbox("Papel", ["user", "admin"])
        submitted = st.form_submit_button("Adicionar Usuário")
        if submitted and new_username and new_password:
            # Simplificado: não verifica duplicidade de username neste demo
            st.session_state.users.append({
                "username": new_username,
                "password": new_password, # Em produção, armazenar hash da senha
                "role": new_role
            })
            st.success(f"Usuário '{new_username}' adicionado com sucesso!")
            st.rerun()

# --- Interface de Usuário Comum ---
def user_dashboard():
    st.sidebar.subheader(f"Bem-vindo, {st.session_state.logged_in_user['username']}")
    user_options = ["Reservar Sala", "Minhas Reuniões"]
    choice = st.sidebar.radio("Menu Usuário", user_options)

    if choice == "Reservar Sala":
        user_book_room()
    elif choice == "Minhas Reuniões":
        user_view_my_meetings()

def user_book_room():
    st.subheader("Reservar Nova Sala")

    with st.form("book_room_form"):
        title = st.text_input("Título da Reunião*", help="Ex: Alinhamento Semanal")
        date = st.date_input("Data*", min_value=datetime.now().date())

        cols_time = st.columns(2)
        with cols_time[0]:
            start_time_val = st.time_input("Horário de Início*", step=timedelta(minutes=15))
        with cols_time[1]:
            end_time_val = st.time_input("Horário de Fim*", step=timedelta(minutes=15))

        available_rooms = [f"{room['name']} (Cap: {room['capacity']})" for room in st.session_state.rooms]
        if not available_rooms:
            st.warning("Nenhuma sala cadastrada. Contate o administrador.")
            st.form_submit_button("Agendar Reunião", disabled=True)
            return

        room_choice_str = st.selectbox("Escolha a Sala*", available_rooms)
        chosen_room_name = room_choice_str.split(" (Cap:")[0]
        chosen_room = next((room for room in st.session_state.rooms if room["name"] == chosen_room_name), None)

        attendees = st.text_input("Participantes (opcional)", help="Nomes ou e-mails separados por vírgula")
        priority = st.selectbox("Prioridade*", ["Baixa", "Média", "Alta"], index=1)

        st.markdown("**Solicitar Itens/Serviços (opcional):**")
        requested_items_list = []
        if st.session_state.requestable_items:
            for item in st.session_state.requestable_items:
                cols_item = st.columns([3,1])
                with cols_item[0]:
                    selected = st.checkbox(f"{item['name']} ({item['description']})", key=f"item_{item['id']}")
                with cols_item[1]:
                    quantity = st.number_input("Qtd", min_value=1, step=1, key=f"qty_{item['id']}", value=1, disabled=not selected, label_visibility="collapsed")
                if selected:
                    requested_items_list.append({"item_id": item["id"], "quantity": quantity})
        else:
            st.caption("Nenhum item disponível para solicitação.")

        submitted = st.form_submit_button("Verificar Disponibilidade e Agendar")

        if submitted:
            if not title:
                st.error("O título da reunião é obrigatório.")
                return
            if not chosen_room:
                st.error("Sala inválida selecionada.") # Should not happen with selectbox
                return
            if end_time_val <= start_time_val:
                st.error("O horário de fim deve ser após o horário de início.")
                return

            if check_room_availability(chosen_room["id"], date, start_time_val, end_time_val, start_time_val, end_time_val):
                new_meeting = {
                    "id": st.session_state.next_meeting_id,
                    "title": title,
                    "room_id": chosen_room["id"],
                    "date": date,
                    "start_time": start_time_val,
                    "end_time": end_time_val,
                    "organizer": st.session_state.logged_in_user["username"],
                    "attendees": attendees,
                    "priority": priority,
                    "requested_items": requested_items_list,
                    "status": "Confirmada"
                }
                st.session_state.meetings.append(new_meeting)
                st.session_state.next_meeting_id += 1
                st.success(f"Reunião '{title}' agendada com sucesso na sala '{chosen_room['name']}' para {date.strftime('%d/%m/%Y')} das {start_time_val.strftime('%H:%M')} às {end_time_val.strftime('%H:%M')}.")
                st.balloons()
                # st.rerun() # Para limpar o formulário, mas perdemos a msg de sucesso imediata.
                           # O clear_on_submit=True na st.form já ajuda.
            else:
                st.error(f"Conflito de horário! A sala '{chosen_room['name']}' já está reservada neste período.")

def user_view_my_meetings():
    st.subheader("Minhas Reuniões Agendadas")
    my_meetings = [m for m in st.session_state.meetings if m["organizer"] == st.session_state.logged_in_user["username"]]

    if not my_meetings:
        st.info("Você não possui nenhuma reunião agendada.")
        return

    meetings_data = []
    for m in my_meetings:
        items_str = ", ".join([f"{req['quantity']}x {get_item_name(req['item_id'])}" for req in m["requested_items"]])
        meetings_data.append({
            "ID": m["id"],
            "Título": m["title"],
            "Sala": get_room_name(m["room_id"]),
            "Data": m["date"].strftime("%d/%m/%Y"),
            "Início": m["start_time"].strftime("%H:%M"),
            "Fim": m["end_time"].strftime("%H:%M"),
            "Prioridade": m["priority"],
            "Itens": items_str if items_str else "Nenhum",
            "Status": m.get("status", "Confirmada")
        })
    df_meetings = pd.DataFrame(meetings_data)
    st.dataframe(df_meetings, use_container_width=True)

    # Funcionalidade de Cancelamento (Simplificada)
    st.markdown("---")
    st.write("**Cancelar Reunião**")
    meeting_ids_to_cancel = [m["id"] for m in my_meetings]
    if meeting_ids_to_cancel:
        meeting_to_cancel_id = st.selectbox("Selecione o ID da reunião para cancelar:", options=meeting_ids_to_cancel)
        if st.button("Cancelar Reunião Selecionada", type="primary"):
            st.session_state.meetings = [m for m in st.session_state.meetings if not (m["id"] == meeting_to_cancel_id and m["organizer"] == st.session_state.logged_in_user["username"])]
            st.success(f"Reunião ID {meeting_to_cancel_id} cancelada.")
            st.rerun()
    else:
        st.caption("Nenhuma reunião para cancelar.")


# --- Lógica Principal do App ---
st.set_page_config(layout="wide", page_title="MVP Agendamento Corporativo")

if st.session_state.logged_in_user:
    st.sidebar.title("Agendamento MVP")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun() # st.experimental_rerun in older versions

    if st.session_state.logged_in_user["role"] == "admin":
        admin_dashboard()
    else:
        user_dashboard()
else:
    login_page()
