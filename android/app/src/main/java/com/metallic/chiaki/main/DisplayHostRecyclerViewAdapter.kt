// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL

package com.metallic.chiaki.main

import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.animation.AnimationUtils
import android.widget.PopupMenu
import androidx.core.view.isGone
import androidx.core.view.isVisible
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.RecyclerView
import com.metallic.chiaki.R
import com.metallic.chiaki.common.DiscoveredDisplayHost
import com.metallic.chiaki.common.DisplayHost
import com.metallic.chiaki.common.ManualDisplayHost
import com.metallic.chiaki.common.ext.inflate
import com.metallic.chiaki.databinding.ItemDisplayHostBinding
import com.metallic.chiaki.lib.DiscoveryHost

class DisplayHostDiffCallback(val old: List<DisplayHost>, val new: List<DisplayHost>): DiffUtil.Callback()
{
    override fun areItemsTheSame(oldItemPosition: Int, newItemPosition: Int) = (old[oldItemPosition] == new[newItemPosition])
    override fun areContentsTheSame(oldItemPosition: Int, newItemPosition: Int) = (old[oldItemPosition] == new[newItemPosition])
    override fun getOldListSize() = old.size
    override fun getNewListSize() = new.size
}

class DisplayHostRecyclerViewAdapter(
    val clickCallback: (DisplayHost) -> Unit,
    val wakeupCallback: (DisplayHost) -> Unit,
    val editCallback: (DisplayHost) -> Unit,
    val deleteCallback: (DisplayHost) -> Unit
): RecyclerView.Adapter<DisplayHostRecyclerViewAdapter.ViewHolder>()
{
    var hosts: List<DisplayHost> = listOf()
        set(value)
        {
            val diff = DiffUtil.calculateDiff(DisplayHostDiffCallback(field, value))
            field = value
            diff.dispatchUpdatesTo(this)
        }

    class ViewHolder(val binding: ItemDisplayHostBinding): RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int)
        = ViewHolder(ItemDisplayHostBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = hosts.count()

    override fun onBindViewHolder(holder: ViewHolder, position: Int)
    {
        val context = holder.itemView.context
        val host = hosts[position]
        holder.binding.also {
            it.nameTextView.text = host.name?.takeIf { name -> name.isNotBlank() } ?: it.root.context.getString(R.string.dv_my_console)
            it.hostTextView.text = it.root.context.getString(R.string.dv_console_address, host.host)
            it.modelText.text = it.root.context.getString(if(host.isPS5) R.string.dv_ps5_model else if(host.isRegistered) R.string.dv_ps4_model else R.string.dv_remote_model)
            it.consoleImage.setImageResource(if(host.isPS5) R.drawable.play_space else R.drawable.ic_deckivo)
            val state = (host as? DiscoveredDisplayHost)?.discoveredHost?.state
            it.statusText.text = when {
                state == DiscoveryHost.State.READY -> it.root.context.getString(R.string.dv_online)
                state == DiscoveryHost.State.STANDBY -> it.root.context.getString(R.string.dv_rest)
                host.isRegistered -> it.root.context.getString(R.string.dv_registered_unknown)
                else -> it.root.context.getString(R.string.dv_registration_needed)
            }
            it.statusText.setTextColor(context.getColor(if(state == DiscoveryHost.State.READY) R.color.accent else R.color.deckivo_warning))
            val app = (host as? DiscoveredDisplayHost)?.discoveredHost?.runningAppName
            it.bottomInfoTextView.text = app?.takeIf { name -> name.isNotBlank() }?.let { name -> it.root.context.getString(R.string.dv_running_app, name) } ?: ""
            it.bottomInfoTextView.visibility = if(it.bottomInfoTextView.text.isEmpty()) View.GONE else View.VISIBLE
            it.playButton.text = if(host.isRegistered) { if(state == DiscoveryHost.State.STANDBY) it.root.context.getString(R.string.dv_wake_play) else it.root.context.getString(R.string.dv_play) } else it.root.context.getString(R.string.dv_register_console)
            val unavailable = host.isRegistered && state != DiscoveryHost.State.READY && state != DiscoveryHost.State.STANDBY
            val help = if (unavailable) context.getString(R.string.dv_offline_help) else null
            if (help != null) { it.bottomInfoTextView.text = help; it.bottomInfoTextView.visibility = View.VISIBLE }
            it.playButton.tooltipText = help
            it.playButton.contentDescription = if (help == null) it.playButton.text else "${it.playButton.text}. $help"
            it.playButton.setOnClickListener { clickCallback(host) }
            it.root.setOnClickListener { clickCallback(host) }

            val canWakeup = host.registeredHost != null
            val canEditDelete = host.manualHost != null
            if(canWakeup || canEditDelete)
            {
                it.menuButton.isVisible = true
                it.menuButton.setOnClickListener { _ ->
                    val menu = PopupMenu(context, it.menuButton)
                    menu.menuInflater.inflate(R.menu.display_host, menu.menu)
                    menu.menu.findItem(R.id.action_wakeup).isVisible = canWakeup
                    menu.menu.findItem(R.id.action_edit).isVisible = canEditDelete
                    menu.menu.findItem(R.id.action_delete).isVisible = canEditDelete
                    menu.setOnMenuItemClickListener { menuItem ->
                        when(menuItem.itemId)
                        {
                            R.id.action_wakeup -> wakeupCallback(host)
                            R.id.action_edit -> editCallback(host)
                            R.id.action_delete -> deleteCallback(host)
                            else -> return@setOnMenuItemClickListener false
                        }
                        true
                    }
                    menu.show()
                }
            }
            else
            {
                it.menuButton.isGone = true
                it.menuButton.setOnClickListener(null)
            }
        }
    }
}
