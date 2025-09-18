import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app as app
from flask_login import login_required
from werkzeug.utils import secure_filename

from models import Aviso
from utils import admin_required
from extensions import db

avisos_bp = Blueprint('avisos', __name__, url_prefix='/avisos', template_folder='templates')

@avisos_bp.route('/admin/avisos/criar', methods=['GET', 'POST'])
@login_required
@admin_required
def criar_aviso():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()
        
        UPLOAD_DIR = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    
        imagem = request.files.get('imagem')
        nome_arquivo = None
        if imagem and imagem.filename:
            nome_arquivo = secure_filename(imagem.filename)
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            imagem.save(caminho)
            caminho = f'uploads/{nome_arquivo}'

        aviso = Aviso(titulo=titulo, conteudo=conteudo, imagem=nome_arquivo)
        db.session.add(aviso)
        db.session.commit()
        flash('Aviso criado com sucesso.', 'success')
        return redirect(url_for('avisos.mural'))
    return render_template('criar_aviso.html')

@avisos_bp.route('/mural')
@login_required
def mural():
    avisos = Aviso.query.order_by(Aviso.criado_em.desc()).all()
    return render_template('mural.html', avisos=avisos)

@avisos_bp.route('/admin/avisos/<int:aviso_id>/deletar', methods=['POST'])
@login_required
@admin_required
def deletar_aviso(aviso_id):
    aviso = Aviso.query.get_or_404(aviso_id)
    db.session.delete(aviso)
    db.session.commit()
    flash('Aviso deletado com sucesso.', 'success')
    return redirect(url_for('avisos.mural'))