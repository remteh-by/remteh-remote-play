// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL
package com.metallic.chiaki.design

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Typeface
import android.view.ContextThemeWrapper
import android.view.View
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import com.metallic.chiaki.R
import com.metallic.chiaki.lan.SafeInsets

/** Shared native components: same spacing, typography and focus states on every Deckivo screen. */
object DeckivoUi {
    fun dp(context: Context, value: Int) = (value * context.resources.displayMetrics.density).toInt()

    fun screen(activity: AppCompatActivity, title: String, description: String): LinearLayout {
        val shell = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.deckivo_background)
        }
        val toolbar = MaterialToolbar(activity).apply {
            this.title = "deckivo"
            setTitleTextColor(activity.getColor(R.color.deckivo_text))
            setNavigationIcon(R.drawable.ic_deckivo_back)
            navigationContentDescription = activity.getString(R.string.dv_back)
            setNavigationOnClickListener { activity.finish() }
            LanguagePicker.addToToolbar(activity, this)
        }
        shell.addView(toolbar, LinearLayout.LayoutParams(-1, dp(activity, 60)))
        val scroll = ScrollView(activity).apply { isFillViewport = true; isVerticalScrollBarEnabled = false }
        val content = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(activity, 28), dp(activity, 12), dp(activity, 28), dp(activity, 28))
        }
        scroll.addView(content)
        shell.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        activity.setContentView(shell)
        SafeInsets.apply(shell)
        label(content, title, 30f, true)
        label(content, description, 15f)
        return content
    }

    fun section(parent: LinearLayout, title: String): LinearLayout {
        val context = parent.context
        val panel = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(context, 20), dp(context, 12), dp(context, 20), dp(context, 20))
            setBackgroundResource(R.drawable.deckivo_panel)
        }
        parent.addView(panel, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(context, 20) })
        label(panel, title, 19f, true)
        return panel
    }

    fun label(parent: LinearLayout, text: String, size: Float = 15f, strong: Boolean = false): TextView = TextView(parent.context).apply {
        this.text = text
        textSize = size
        typeface = Typeface.create(androidx.core.content.res.ResourcesCompat.getFont(context, R.font.ibm_plex_sans), if(strong) Typeface.BOLD else Typeface.NORMAL)
        setTextColor(context.getColor(if(strong) R.color.deckivo_text else R.color.deckivo_muted))
        setPadding(0, dp(context, 7), 0, dp(context, 7))
        setLineSpacing(dp(context, 3).toFloat(), 1f)
        parent.addView(this, LinearLayout.LayoutParams(-1, -2))
    }

    fun button(parent: LinearLayout, text: String, primary: Boolean = false, action: () -> Unit): MaterialButton {
        val style = if(primary) R.style.Deckivo_Button else R.style.Deckivo_Button_Secondary
        return MaterialButton(ContextThemeWrapper(parent.context, style), null, 0).apply {
            this.text = text
            isAllCaps = false
            textSize = 15f
            cornerRadius = dp(context, 14)
            insetTop = 0; insetBottom = 0
            minHeight = dp(context, 52)
            backgroundTintList = context.getColorStateList(if(primary) R.color.deckivo_button_bg else R.color.deckivo_secondary_bg)
            setTextColor(context.getColor(if(primary) R.color.deckivo_ink else R.color.deckivo_text))
            strokeColor = context.getColorStateList(R.color.deckivo_focus_stroke)
            strokeWidth = dp(context, 1)
            setOnClickListener { action() }
            parent.addView(this, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(context, 10) })
        }
    }

    fun field(parent: LinearLayout, hint: String, value: String, digits: Boolean = false): TextInputEditText {
        val wrapper = TextInputLayout(parent.context).apply {
            this.hint = hint
            boxBackgroundMode = TextInputLayout.BOX_BACKGROUND_OUTLINE
            setBoxCornerRadii(dp(context, 14).toFloat(), dp(context, 14).toFloat(), dp(context, 14).toFloat(), dp(context, 14).toFloat())
            boxStrokeColor = context.getColor(R.color.accent)
            defaultHintTextColor = ColorStateList.valueOf(context.getColor(R.color.deckivo_muted))
        }
        val field = TextInputEditText(wrapper.context).apply {
            setText(value)
            textSize = 16f
            setSingleLine(true)
            inputType = if(digits) android.text.InputType.TYPE_CLASS_NUMBER else android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
            importantForAutofill = View.IMPORTANT_FOR_AUTOFILL_NO
        }
        wrapper.addView(field, LinearLayout.LayoutParams(-1, -2))
        parent.addView(wrapper, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(parent.context, 12) })
        return field
    }
}
