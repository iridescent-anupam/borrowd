from typing import Any, cast

from django import forms
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from borrowd.models import TrustLevel
from borrowd_groups.models import BorrowdGroup
from borrowd_users.models import BorrowdUser

DUPLICATE_GROUP_NAME_ERROR = "You already have a group with this name."


class GroupCreateForm(forms.ModelForm[BorrowdGroup]):
    user: BorrowdUser | AnonymousUser | None

    trust_level = forms.ChoiceField(
        choices=sorted(TrustLevel.choices, reverse=True),
        required=True,
        label="How trusted should this group be?",
        initial=TrustLevel.HIGH,
        widget=forms.Select(
            attrs={
                "class": "block py-[10.5px] pl-3 appearance-none w-full box-border",
            }
        ),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.user = cast(BorrowdUser | AnonymousUser | None, kwargs.pop("user", None))
        super().__init__(*args, **kwargs)

    def clean_name(self) -> str:
        name = cast(str, self.cleaned_data["name"])

        if not isinstance(self.user, BorrowdUser):
            return name

        duplicate_exists = (
            BorrowdGroup.objects.filter(
                created_by=self.user,
                name=name,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        )

        if duplicate_exists:
            raise ValidationError(DUPLICATE_GROUP_NAME_ERROR)

        return name

    class Meta:
        model = BorrowdGroup

        fields = [
            "name",
            "description",
            "trust_level",
            "banner",
            "membership_requires_approval",
        ]

        labels = {
            "name": "Group name",
            "description": "Group description",
            "banner": "Banner (optional)",
            "membership_requires_approval": "",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "flex justify-center items-center gap-[10px] w-full py-[10.5px] px-3",
                    "placeholder": "100 Broadway Ave Neighbors",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "block w-full h-20 px-3 py-2 box-border",
                    "placeholder": "Enter a helpful description for your group",
                }
            ),
            "logo": forms.FileInput(attrs={"class": "hidden", "id": "logo-upload"}),
            "banner": forms.ClearableFileInput(
                attrs={
                    "class": (
                        "block w-full text-sm text-gray-600 file:font-semibold "
                        "file:mr-3 file:py-2 file:px-4 "
                        "file:rounded-md file:border-0 "
                        "file:bg-gray-100 file:text-gray-900 "
                        "hover:file:bg-gray-200 "
                    )
                }
            ),
            "membership_requires_approval": forms.CheckboxInput(
                attrs={
                    "class": "h-5 w-5 rounded-md border-gray-300 text-black focus:ring-0",
                }
            ),
        }


class GroupJoinForm(forms.Form):
    trust_level = forms.ChoiceField(
        choices=TrustLevel.choices,
        required=True,
        label="Your Trust Level with this Group",
    )


class UpdateTrustLevelForm(forms.Form):
    trust_level = forms.ChoiceField(
        choices=TrustLevel.choices,
        required=True,
        label="Your Trust Level with this Group",
        help_text="Update your trust level to control what items you share with this group.",
    )
