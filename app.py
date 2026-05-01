from flask import Flask, render_template, request, redirect, os
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_NAME = "cafe-app.db"


# DB接続
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# 商品一覧
# =========================
@app.route("/products")
def product_list():

    conn = get_db()

    products = conn.execute("""
        SELECT
            products.id,
            products.name,
            units.name AS unit_name,
            products.stock
        FROM products
        LEFT JOIN units
        ON products.unit_id = units.id
        ORDER BY products.id
    """).fetchall()

    conn.close()

    return render_template(
        "product_list.html",
        products=products
    )


# =========================
# 商品登録
# =========================
@app.route("/products/new")
def product_form():

    conn = get_db()

    units = conn.execute(
        "SELECT * FROM units"
    ).fetchall()

    conn.close()

    return render_template(
        "product_form.html",
        units=units
    )


@app.route("/products/create", methods=["POST"])
def product_create():

    name = request.form.get("name")
    unit_id = request.form.get("unit_id")

    conn = get_db()

    conn.execute("""
        INSERT INTO products (
            name,
            unit_id,
            stock
        )
        VALUES (?, ?, 0)
    """, (name, unit_id))

    conn.commit()
    conn.close()

    return redirect("/products")


# =========================
# 入出庫登録画面（商品指定対応）
# =========================

@app.route("/stock/new")
@app.route("/stock/new/<int:product_id>")
def stock_form(product_id=None):

    conn = get_db()

    products = conn.execute(
        "SELECT * FROM products"
    ).fetchall()

    statuses = conn.execute(
        "SELECT * FROM stock_status"
    ).fetchall()

    conn.close()

    return render_template(
        "stock_form.html",
        products=products,
        statuses=statuses,
        selected_product_id=product_id
    )


# =========================
# ★ 入出庫登録処理
# =========================
@app.route("/stock/create", methods=["POST"])
def stock_create():

    product_id = request.form.get("product_id")
    status_id = request.form.get("status_id")
    quantity = int(request.form.get("quantity"))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()

    # 履歴登録
    conn.execute("""
        INSERT INTO stock_logs (
            product_id,
            status_id,
            quantity,
            datetime
        )
        VALUES (?, ?, ?, ?)
    """, (product_id, status_id, quantity, now))

    # 在庫更新
    if status_id == "1":  # 入庫
        conn.execute("""
            UPDATE products
            SET stock = stock + ?
            WHERE id = ?
        """, (quantity, product_id))

    elif status_id == "2":  # 出庫
        conn.execute("""
            UPDATE products
            SET stock = stock - ?
            WHERE id = ?
        """, (quantity, product_id))

    conn.commit()
    conn.close()

    return redirect("/products")


# =========================
# ★ 入出庫履歴
# =========================
@app.route("/stock/logs")
def stock_logs():

    conn = get_db()

    logs = conn.execute("""
        SELECT
            stock_logs.id,
            products.name AS product_name,
            stock_status.status,
            stock_logs.quantity,
            stock_logs.datetime
        FROM stock_logs
        LEFT JOIN products
        ON stock_logs.product_id = products.id
        LEFT JOIN stock_status
        ON stock_logs.status_id = stock_status.id
        ORDER BY stock_logs.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "stock_logs.html",
        logs=logs
    )
# =========================
# 商品編集画面
# =========================
@app.route("/products/edit/<int:id>")
def product_edit(id):

    conn = get_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (id,)
    ).fetchone()

    units = conn.execute(
        "SELECT * FROM units"
    ).fetchall()

    conn.close()

    return render_template(
        "product_edit.html",
        product=product,
        units=units
    )


# =========================
# 商品更新処理
# =========================
@app.route("/products/update/<int:id>", methods=["POST"])
def product_update(id):

    name = request.form.get("name")
    unit_id = request.form.get("unit_id")

    conn = get_db()

    conn.execute("""
        UPDATE products
        SET name = ?,
            unit_id = ?
        WHERE id = ?
    """, (name, unit_id, id))

    conn.commit()
    conn.close()

    return redirect("/products")


# =========================
# 商品削除
# =========================
@app.route("/products/delete/<int:id>")
def product_delete(id):

    conn = get_db()

    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/products")
# =========================
# 単位一覧
# =========================
@app.route("/units")
def unit_list():

    conn = get_db()

    units = conn.execute(
        "SELECT * FROM units ORDER BY id"
    ).fetchall()

    conn.close()

    return render_template(
        "unit_list.html",
        units=units
    )


# =========================
# 単位登録画面
# =========================
@app.route("/units/new")
def unit_form():

    return render_template(
        "unit_form.html"
    )


# =========================
# 単位登録処理
# =========================
@app.route("/units/create", methods=["POST"])
def unit_create():

    name = request.form.get("name")

    conn = get_db()

    conn.execute(
        "INSERT INTO units (name) VALUES (?)",
        (name,)
    )

    conn.commit()
    conn.close()

    return redirect("/units")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)