import streamlit as st
import math, random, csv, io

# =================== CẤU HÌNH STREAMLIT ======================
st.set_page_config(page_title="Thuật giải Sudoku", layout="wide")

# =================== CSS GIỐNG GIAO DIỆN TKINTER =============
st.markdown("""
<style>
    body {
        background-color: #f0f4fa;
    }
    .title-main {
        text-align: center;
        font-size: 30px;
        font-weight: bold;
        color: #0b5394;
        margin-bottom: 10px;
    }
    .panel-start {
        background-color: #EAF6FF;
        padding: 25px;
        border-radius: 14px;
        width: 90%;
        margin: auto;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    .note-text {
        text-align: center;
        font-size: 11px;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# =================== THUẬT TOÁN SUDOKU (TỪ BẢN CŨ) ===================
def valid_in_board(board, n, box_size, row, col, num):
    for k in range(n):
        if board[row][k] == num:
            return False
        if board[k][col] == num:
            return False
    start_r = row - row % box_size
    start_c = col - col % box_size
    for i in range(box_size):
        for j in range(box_size):
            if board[start_r + i][start_c + j] == num:
                return False
    return True

def solve_backtrack(board, n, box_size):
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                for num in range(1, n + 1):
                    if valid_in_board(board, n, box_size, r, c, num):
                        board[r][c] = num
                        if solve_backtrack(board, n, box_size):
                            return True
                        board[r][c] = 0
                return False
    return True

def generate_full_board(n):
    box_size = int(math.sqrt(n))
    board = [[0] * n for _ in range(n)]
    nums = list(range(1, n + 1))

    def helper(pos=0):
        if pos == n * n:
            return True
        r = pos // n
        c = pos % n
        random.shuffle(nums)
        for num in nums:
            if valid_in_board(board, n, box_size, r, c, num):
                board[r][c] = num
                if helper(pos + 1):
                    return True
                board[r][c] = 0
        return False

    ok = helper()
    if not ok:
        raise RuntimeError("Không tạo được board hoàn chỉnh — thử lại.")
    return board

def remove_cells_for_difficulty(board, difficulty):
    n = len(board)
    puzzle = [row[:] for row in board]
    total = n * n

    if n == 9:
        if difficulty == "Dễ":
            remove = 40
        elif difficulty == "Trung bình":
            remove = 50
        else:
            remove = 60
    elif n == 16:
        if difficulty == "Dễ":
            remove = int(total * 0.55)
        elif difficulty == "Trung bình":
            remove = int(total * 0.65)
        else:
            remove = int(total * 0.75)
    else:  # 25
        if difficulty == "Dễ":
            remove = int(total * 0.5)
        elif difficulty == "Trung bình":
            remove = int(total * 0.65)
        else:
            remove = int(total * 0.8)

    remove = min(remove, total - 1)
    cells = [(r, c) for r in range(n) for c in range(n)]
    random.shuffle(cells)
    removed = 0
    for (r, c) in cells:
        if removed >= remove:
            break
        puzzle[r][c] = 0
        removed += 1
    return puzzle

# =================== HÀM HỖ TRỢ ===================
def empty_board(n):
    return [[0] * n for _ in range(n)]

def init_puzzle():
    size_text = st.session_state["size_text"]
    n = int(size_text.split("x")[0])
    box = int(math.sqrt(n))
    level = st.session_state["level"]
    source = st.session_state["source"]

    if source == "Tạo ngẫu nhiên":
        full = generate_full_board(n)
        puzzle = remove_cells_for_difficulty(full, level)
    elif source == "Tự nhập thủ công":
        puzzle = empty_board(n)
    else:  # CSV
        csv_content = st.session_state.get("csv_content", None)
        if not csv_content:
            st.session_state["error_msg"] = "Chưa có dữ liệu CSV hợp lệ."
            puzzle = empty_board(n)
        else:
            reader = csv.reader(io.StringIO(csv_content))
            rows = []
            for row in reader:
                if not any(cell.strip() for cell in row):
                    continue
                tokens = [tok.strip() for tok in row if tok.strip() != ""]
                rows.append([int(tok) for tok in tokens])
            if len(rows) != n or any(len(r) != n for r in rows):
                st.session_state["error_msg"] = f"File CSV phải là ma trận {n}x{n}."
                puzzle = empty_board(n)
            else:
                puzzle = rows

    st.session_state["grid_size"] = n
    st.session_state["box_size"] = box
    st.session_state["initial_board"] = [row[:] for row in puzzle]
    st.session_state["board"] = [row[:] for row in puzzle]
    st.session_state["need_new_puzzle"] = False

def check_current_answer(board, initial, n, box_size):
    for r in range(n):
        for c in range(n):
            if initial[r][c] == 0 and board[r][c] != 0:
                val = board[r][c]
                if not (1 <= val <= n):
                    return False, f"Số ở ô ({r+1},{c+1}) phải trong khoảng 1..{n}"
                tmp = board[r][c]
                board[r][c] = 0
                if not valid_in_board(board, n, box_size, r, c, val):
                    board[r][c] = tmp
                    return False, f"Số {val} tại ô ({r+1},{c+1}) đang bị trùng hàng/cột/ô con."
                board[r][c] = tmp
    return True, "✓ Đáp án hiện tại hợp lệ!"

# =================== STATE BAN ĐẦU ===================
if "started" not in st.session_state:
    st.session_state.started = False
if "need_new_puzzle" not in st.session_state:
    st.session_state.need_new_puzzle = False

# =================== MÀN HÌNH START ===================
if not st.session_state.started:
    st.markdown("<div class='title-main'>Thuật giải game Sudoku</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='panel-start'>", unsafe_allow_html=True)

        col_left, col_mid, col_right = st.columns([1, 2, 1])

        with col_mid:
            size_text = st.selectbox("Chọn kích thước:", ["9x9", "16x16", "25x25"])
            level = st.selectbox("Chọn mức độ:", ["Dễ", "Trung bình", "Khó"])
            source = st.selectbox("Nguồn đề:", ["Tạo ngẫu nhiên", "Tự nhập thủ công", "Mở file CSV"])
            csv_file = None
            csv_content = None
            if source == "Mở file CSV":
                csv_file = st.file_uploader("Chọn file CSV (0 = ô trống)", type=["csv"])
                if csv_file is not None:
                    csv_content = csv_file.getvalue().decode("utf-8")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<p class='note-text'>Ghi chú: CSV định dạng mỗi hàng một dòng, phân tách bằng dấu phẩy. 0 = ô trống.</p>", unsafe_allow_html=True)

    start_clicked = st.button("Bắt đầu", type="primary")

    if start_clicked:
        st.session_state.started = True
        st.session_state.size_text = size_text
        st.session_state.level = level
        st.session_state.source = source
        if csv_file is not None:
            st.session_state.csv_content = csv_content
        else:
            st.session_state.csv_content = None
        st.session_state.need_new_puzzle = True
        st.session_state.error_msg = ""
        st.rerun()

    st.stop()

# =================== MÀN HÌNH GIẢI SUDOKU ===================
if st.session_state.need_new_puzzle:
    init_puzzle()

n = st.session_state["grid_size"]
box_size = st.session_state["box_size"]
initial_board = st.session_state["initial_board"]
board = st.session_state["board"]

st.markdown("<div class='title-main'>Thuật giải game Sudoku</div>", unsafe_allow_html=True)

top_left, top_right = st.columns([4, 1])
with top_right:
    if st.button("⬅ Quay lại màn hình chọn"):
        st.session_state.started = False
        st.rerun()

if st.session_state.get("error_msg"):
    st.error(st.session_state["error_msg"])

col_board, col_ctrl = st.columns([3, 1])

# ----------------- BẢNG SUDOKU (DÙNG text_input, KHÔNG CÒN BẢNG ẨN) -----------------
grid = []

with col_board:
    st.write("")
    for r in range(n):
        row_vals = []
        cols = st.columns(n)
        for c in range(n):
            key = f"cell_{r}_{c}"
            current_val = board[r][c]
            default_str = "" if current_val == 0 else str(current_val)

            # khởi tạo state cho ô này nếu chưa có
            if key not in st.session_state:
                st.session_state[key] = default_str

            disabled = initial_board[r][c] != 0
            bg_color = "#ecf6ff" if ((r // box_size) + (c // box_size)) % 2 == 0 else "#ffffff"

            val_str = cols[c].text_input(
                "",
                value=st.session_state[key],
                max_chars=1,
                key=key,
                disabled=disabled,
            )

            # cập nhật lại state (phòng trường hợp value ban đầu khác)
            st.session_state[key] = val_str
            row_vals.append(int(val_str) if val_str.isdigit() else 0)
        grid.append(row_vals)

# cập nhật board từ grid người dùng nhập
st.session_state["board"] = [row[:] for row in grid]
board = st.session_state["board"]

# ----------------- PANEL ĐIỀU KHIỂN -----------------
with col_ctrl:
    st.subheader("Chức năng")
    st.caption("📌 Hệ thống sẽ đọc toàn bộ ô (0 = ô trống) khi bạn bấm nút.")

    with st.form("actions_form"):
        action = st.selectbox(
            "Chọn hành động:",
            ["Giải nhanh", "Kiểm tra đáp án", "Reset về đề ban đầu"]
        )
        submitted = st.form_submit_button("Thực hiện")

# ----------------- XỬ LÝ NÚT -----------------
if submitted:
    # luôn lấy board hiện tại từ session_state
    board = [row[:] for row in st.session_state["board"]]

    if action == "Reset về đề ban đầu":
        st.session_state["board"] = [row[:] for row in initial_board]
        # cập nhật lại từng ô text_input
        for r in range(n):
            for c in range(n):
                key = f"cell_{r}_{c}"
                val = initial_board[r][c]
                st.session_state[key] = "" if val == 0 else str(val)
        st.success("Đã reset về đề ban đầu.")
        st.rerun()

    elif action == "Kiểm tra đáp án":
        ok, msg = check_current_answer(
            [row[:] for row in board],
            initial_board,
            n,
            box_size
        )
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    elif action == "Giải nhanh":
        temp = [row[:] for row in board]
        solved = solve_backtrack(temp, n, box_size)
        if solved:
            st.session_state["board"] = [row[:] for row in temp]
            # cập nhật text_input theo lời giải
            for r in range(n):
                for c in range(n):
                    key = f"cell_{r}_{c}"
                    st.session_state[key] = str(temp[r][c])
            st.success("✓ Đã giải xong Sudoku!")
            st.rerun()
        else:
            st.error("Không thể giải được bài này.")
