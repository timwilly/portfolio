from flask import render_template, url_for
from app.about_me import bp


@bp.route('/about_me')
def about_me():
    image_file_me = url_for('static', filename='pictures/willy.JPG')
    image_file_photography_1 = url_for('static', filename='pictures/vieux_port.jpg')
    image_file_photography_2 = url_for('static', filename='pictures/mont_tremblant.jpg')
    image_file_photography_3 = url_for('static', filename='pictures/mont_tremblant_2.jpg')
    image_file_photography_4 = url_for('static', filename='pictures/mont_tremblant_3.jpg')
    image_file_photography_5 = url_for('static', filename='pictures/parc_jeandrapeau.jpg')
    image_file_photography_6 = url_for('static', filename='pictures/complexe_desjardins.jpg')
    image_file_photography_7 = url_for('static', filename='pictures/vieux_port_2.jpg')
    image_file_photography_8 = url_for('static', filename='pictures/balcon.jpg')
    return render_template('about_me/about_me.html',
                           image_file_me=image_file_me,
                           image_file_photography_1=image_file_photography_1,
                           image_file_photography_2=image_file_photography_2,
                           image_file_photography_3=image_file_photography_3,
                           image_file_photography_4=image_file_photography_4,
                           image_file_photography_5=image_file_photography_5,
                           image_file_photography_6=image_file_photography_6,
                           image_file_photography_7=image_file_photography_7,
                           image_file_photography_8=image_file_photography_8
                           )
