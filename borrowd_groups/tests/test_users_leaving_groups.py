from django.test import TestCase
from django.urls import reverse

from borrowd.models import TrustLevel
from borrowd_groups.models import BorrowdGroup, Membership
from borrowd_items.models import Item, ItemCategory, Transaction, TransactionStatus
from borrowd_users.models import BorrowdUser


class UsersLeavingGroupsTests(TestCase):
    """
    Tests for the leave-group flow.

    Standard members can leave a group.
    Moderators cannot leave through this flow.
    Members with active transactions cannot leave.

    Moderator handoff flow belong to later iterations once that functionality exists.
    """

    def setUp(self) -> None:
        # Arrange
        # Create users for the group and transaction.
        self.owner = BorrowdUser.objects.create_user(
            username="owner",
            password="password",
        )
        self.member = BorrowdUser.objects.create_user(
            username="member",
            password="password",
        )
        self.other_user = BorrowdUser.objects.create_user(
            username="other",
            password="password",
        )

        # Create a group where the owner is the default moderator and
        # the member is a standard member.
        self.group: BorrowdGroup = BorrowdGroup.objects.create(
            name="Test Group",
            created_by=self.owner,
            updated_by=self.owner,
            trust_level=TrustLevel.STANDARD,
            membership_requires_approval=False,
        )
        self.group.add_user(self.member, trust_level=TrustLevel.STANDARD)

    def test_member_can_leave_group(self) -> None:
        # Arrange
        self.client.force_login(self.member)

        # Act
        response = self.client.post(
            reverse("borrowd_groups:leave-group", args=[self.group.pk])
        )

        # Assert
        # The member should be redirected back to the group list and
        # their membership should be removed.
        self.assertRedirects(response, reverse("borrowd_groups:group-list"))
        self.assertFalse(
            Membership.objects.filter(user=self.member, group=self.group).exists()
        )

    def test_non_member_cannot_leave_group(self) -> None:
        # Arrange
        self.client.force_login(self.other_user)

        # Act
        response = self.client.post(
            reverse("borrowd_groups:leave-group", args=[self.group.pk])
        )

        # Assert
        # A non-member should not be able to leave a group they do not belong to.
        self.assertRedirects(
            response,
            reverse("borrowd_groups:group-detail", args=[self.group.pk]),
            target_status_code=403,
        )
        self.assertFalse(
            Membership.objects.filter(user=self.other_user, group=self.group).exists()
        )

    def test_moderator_cannot_leave_group(self) -> None:
        # Arrange
        # The owner is the group's default moderator.
        self.client.force_login(self.owner)

        # Act
        response = self.client.post(
            reverse("borrowd_groups:leave-group", args=[self.group.pk])
        )

        # Assert
        # Moderators are currently blocked from leaving through this flow.
        self.assertRedirects(
            response,
            reverse("borrowd_groups:group-detail", args=[self.group.pk]),
        )
        self.assertTrue(
            Membership.objects.filter(user=self.owner, group=self.group).exists()
        )

    def test_member_with_active_transaction_cannot_leave_group(self) -> None:
        # Arrange
        # Create an item and an active transaction involving the member.
        category = ItemCategory.objects.create(
            name="Tools",
            description="Tools category",
        )
        item = Item.objects.create(
            name="Drill",
            description="Cordless drill",
            owner=self.owner,
            trust_level_required=TrustLevel.STANDARD,
        )
        item.categories.add(category)

        Transaction.objects.create(
            item=item,
            party1=self.owner,
            party2=self.member,
            status=TransactionStatus.REQUESTED,
            updated_by=self.member,
        )

        self.client.force_login(self.member)

        # Act
        response = self.client.post(
            reverse("borrowd_groups:leave-group", args=[self.group.pk])
        )

        # Assert
        # Members with active transactions must stay in the group until
        # those transactions are resolved.
        self.assertRedirects(
            response,
            reverse("borrowd_groups:group-detail", args=[self.group.pk]),
        )
        self.assertTrue(
            Membership.objects.filter(user=self.member, group=self.group).exists()
        )
