if [ -z "$TEST" ]; then
    echo ""
    echo "Missing required test env" >&2
    echo "export TEST=<dir> to run specified tests" >&2
    echo ""
    exit
fi

if [ -e /root/agent ]; then
    source /root/agent > /dev/null
fi

if [ -z "$TMPDIR" ]; then
    export TMPDIR=$(mktemp -d)
    chmod go+rwx "$TMPDIR"
fi

load "$TEST"/config.bash


setup() {
 aa-teardown >/dev/null || true
}

@test "Create VM image in ${TMPDIR}/${VM_IMAGE} based on $IMAGE_URL" {
    # setup and create image with filesystem
    mkdir -p "${TMPDIR}"/empty
    curl -o "$TMPDIR"/alpine.tar.gz "$IMAGE_URL"
    gunzip "$TMPDIR"/alpine.tar.gz
    rm -f  "${TMPDIR}"/"${VM_IMAGE}"
    run virt-make-fs --partition --type=ext4 --size=+2G --format=qcow2 "${TMPDIR}"/alpine.tar "${TMPDIR}"/"${VM_IMAGE}"
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run modprobe nbd
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Setup: Define and start test VM ${VM}" {
    virsh destroy "${VM}" || true
    echo "output = ${output}"
    virsh undefine "${VM}" --remove-all-storage --checkpoints-metadata || true
    echo "output = ${output}"
    cp "${VM}"/"${VM}".xml "${TMPDIR}"/
    sed -i "s|__TMPDIR__|${TMPDIR}|g" "${TMPDIR}"/"${VM}".xml
    run virsh define "${TMPDIR}"/"${VM}".xml
    echo "output = ${output}"
    run virsh start "${VM}"
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    echo "output = ${output}"
}
@test "Backup: create full backup" {
    run ../virtnbdbackup -d "$VM" -l full -o "${TMPDIR}"/fstrim
    echo "output = ${output}"
    [[ "${output}" =~  "Saved qcow image config" ]]
    [ "$status" -eq 0 ]
}
@test "Destroy VM" {
    run virsh destroy "$VM"
    [ "$status" -eq 0 ]
}
@test "Map image via NBD, run fstrim" {
    run qemu-nbd -c /dev/nbd5 "${TMPDIR}"/"${VM_IMAGE}" --cache=directsync --discard=unmap
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run sleep 5 && mount /dev/nbd5p1 "${TMPDIR}"/empty
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run fstrim -v "${TMPDIR}"/empty/
    echo "trimmed = ${output}" >&3
    [ "$status" -eq 0 ]
    run umount "${TMPDIR}"/empty
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run qemu-nbd -d /dev/nbd5p1
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Start VM" {
    run virsh start "$VM"
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Backup: incremental backup" {
    run ../virtnbdbackup -d "$VM" -l inc -o "${TMPDIR}"/fstrim
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Destroy VM 2" {
    run virsh destroy "$VM"
    [ "$status" -eq 0 ]
}
@test "Map image via NBD, create data, delete data, run fstrim" {
    run qemu-nbd -c /dev/nbd5 "${TMPDIR}"/"${VM_IMAGE}" --cache=directsync --discard=unmap
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run sleep 5 && mount /dev/nbd5p1 "${TMPDIR}"/empty
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run cp -a "${TMPDIR}"/empty/etc "${TMPDIR}"/empty/etc_before_fstrim2 && sync
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run rm -rf "${TMPDIR}"/empty/* && sync
    run umount "${TMPDIR}"/empty
    run sleep 5 && mount /dev/nbd5p1 "${TMPDIR}"/empty
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run fstrim -v "${TMPDIR}"/empty
    echo "trimmed = ${output}" >&3
    [ "$status" -eq 0 ]
    run tar -xf "${TMPDIR}"/alpine.tar -C "${TMPDIR}"/empty/ && sync
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run umount "${TMPDIR}"/empty
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run qemu-nbd -d /dev/nbd5p1
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Copy image for reference" {
    run cp "${TMPDIR}"/"${VM_IMAGE}" "${TMPDIR}"/reference_before_backup.qcow2
    [ "$status" -eq 0 ]
}
@test "Start VM again" {
    run virsh start "$VM"
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Backup: incremental backup again" {
    run ../virtnbdbackup -d "$VM" -l inc -o "${TMPDIR}"/fstrim
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Restore" {
    run ../virtnbdrestore -i "${TMPDIR}"/fstrim -o "${TMPDIR}"/restore
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
@test "Run filesystem check in restored image" {
    run guestfish -a "${TMPDIR}"/restore/fstest.qcow2 <<_EOF_
run
fsck ext4 /dev/sda1
_EOF_
    [ "$status" -eq 0 ]
    [[ "${output}" = "0" ]]
}
@test "Compare data in reference image against restored image" {
    run guestfish -a  "${TMPDIR}"/reference_before_backup.qcow2  -m /dev/sda1 tar-out / "${TMPDIR}"/reference_data.tar
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run guestfish -a  "${TMPDIR}"/restore/fstest.qcow2  -m /dev/sda1 tar-out / "${TMPDIR}"/restore_data.tar
    echo "output = ${output}"
    [ "$status" -eq 0 ]
    run cmp "${TMPDIR}"/restore_data.tar "${TMPDIR}"/reference_data.tar
    echo "output = ${output}"
    [ "$status" -eq 0 ]
}
