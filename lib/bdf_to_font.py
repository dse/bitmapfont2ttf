class BDFToFont:
    def convert_to_sfd(bdf_font):
        font = fontforge.font()
        font.em                     = bdf_font.get_pixel_size()
        [font.ascent, font.descent] = compute_new_ascent_descent(bdf_font)
        font.comment                = "\n".join(bdf_font.get_comments())
        font.copyright              = bdf_font.get_copyright()
        font.familyname             = bdf_font.get_family_name()
        font.fontname               = bdf_font.get_font_name()
        font.fullname               = bdf_font.get_full_name()
        font.italic_angle           = bdf_font.get_italic_angle()
        font.os2_subxoff            = bdf_font.get_subscript_x_offset()
        font.os2_subxsize           = bdf_font.get_subscript_x_size()
        font.os2_subyoff            = bdf_font.get_subscript_y_offset()
        font.os2_subysize           = bdf_font.get_subscript_y_size()
        font.os2_supxoff            = bdf_font.get_superscript_x_offset()
        font.os2_supxsize           = bdf_font.get_superscript_x_size()
        font.os2_supyoff            = bdf_font.get_superscript_y_offset()
        font.os2_supysize           = bdf_font.get_superscript_y_size()
        font.upos                   = bdf_font.get_underline_position()
        font.uwidth                 = bdf_font.get_underline_width()
        font.version                = bdf_font.get_version_string()
        font.weight                 = bdf_font.get_weight()
    def compute_new_ascent_descent(bdf_font):
        ascent = bdf_font.get_ascent()
        descent = bdf_font.get_descent()
        em = bdf_font.get_pixel_size()
        if ascent + descent == em:
            return [ascent, descent]
        diff = abs(em - ascent - descent)
        if ascent + descent < em:
            max_ascent  = ascent + diff
            min_descent = descent
            max_descent = descent + diff
            min_ascent  = ascent
        else:
            max_ascent  = ascent
            min_descent = descent - diff
            min_ascent  = ascent - diff
            max_descent = descent
            if min_descent < 0:
                max_ascent -= min_descent
                min_descent = 0
            if min_ascent < 0:
                max_descent -= min_ascent
                min_ascent = 0
        pixel_counts = []
        for new_ascent in range(min_ascent, max_ascent + 1):
            pixel_counts[new_ascent] = 0
            high_row = new_ascent
            low_row = new_ascent - em + 1
            for row in range(low_row, high_row + 1):
                pixel_counts[new_ascent] += bdf_font.get_pixel_count(row)
        max_pixel_count = max(*[pixel_counts[i] for i in range(min_ascent, max_ascent + 1)])
        new_ascent_candidates = [i for i in range(min_ascent, max_ascent + 1) if pixel_counts[i] == max_pixel_count]
        new_ascent = max(*new_ascent_candidates)
        new_descent = em - new_ascent
        return [new_ascent, new_descent]
